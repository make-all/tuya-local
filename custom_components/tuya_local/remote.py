"""
Implementation of Tuya remote control devices
Based on broadlink integration for code saving under HA storage
"""
import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Iterable
from datetime import timedelta
from itertools import product
from typing import Any

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.components.remote import (
    ATTR_ALTERNATIVE,
    ATTR_DELAY_SECS,
    ATTR_DEVICE,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    SERVICE_DELETE_COMMAND,
    SERVICE_LEARN_COMMAND,
    SERVICE_SEND_COMMAND,
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.components.remote import (
    DOMAIN as RM_DOMAIN,
)
from homeassistant.const import ATTR_COMMAND
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

# from tinytuya.Contrib.IRRemoteControlDevice import (
#     base64_to_pulses,
#     pulses_to_pronto,
#     pulses_to_width_encoded,
# )
from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)

CODE_STORAGE_VERSION = 1
FLAG_STORAGE_VERSION = 1

CODE_SAVE_DELAY = 15
FLAG_SAVE_DELAY = 15

LEARNING_TIMEOUT = timedelta(seconds=30)

# These commands seem to be standard for all devices
CMD_SEND = "send_ir"
CMD_LEARN = "study"
CMD_ENDLEARN = "study_exit"
CMD_STUDYKEY = "study_key"

COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_COMMAND): vol.All(
            cv.ensure_list, [vol.All(cv.string, vol.Length(min=1))], vol.Length(min=1)
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SEND_SCHEMA = COMMAND_SCHEMA.extend(
    {
        vol.Optional(ATTR_DEVICE): vol.All(cv.string, vol.Length(min=1)),
        vol.Optional(ATTR_DELAY_SECS, default=DEFAULT_DELAY_SECS): vol.Coerce(float),
    }
)
SERVICE_LEARN_SCHEMA = COMMAND_SCHEMA.extend(
    {
        vol.Required(ATTR_DEVICE): vol.All(cv.string, vol.Length(min=1)),
        vol.Optional(ATTR_ALTERNATIVE, default=False): cv.boolean,
    }
)
SERVICE_DELETE_SCHEMA = COMMAND_SCHEMA.extend(
    {
        vol.Required(ATTR_DEVICE): vol.All(cv.string, vol.Length(min=1)),
    }
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "remote",
        TuyaLocalRemote,
    )


class TuyaLocalRemote(TuyaLocalEntity, RemoteEntity):
    """Representation of a Tuya Remote entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the remote device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._send_dp = dps_map.pop("send", None)
        self._receive_dp = dps_map.pop("receive", None)
        # Some remotes split out the control (command) into its own dp and just send raw codes in send
        self._control_dp = dps_map.pop("control", None)
        self._delay_dp = dps_map.pop("delay", None)
        self._type_dp = dps_map.pop("code_type", None)
        self._init_end(dps_map)
        if self._receive_dp:
            self._attr_supported_features |= (
                RemoteEntityFeature.LEARN_COMMAND | RemoteEntityFeature.DELETE_COMMAND
            )
        self._code_storage = Store(
            device._hass,
            CODE_STORAGE_VERSION,
            f"tuya_local_remote_{device.unique_id}_codes",
        )
        self._flag_storage = Store(
            device._hass,
            FLAG_STORAGE_VERSION,
            f"tuya_local_remote_{device.unique_id}_flags",
        )
        self._storage_loaded = False
        self._codes = {}
        self._flags = defaultdict(int)
        self._lock = asyncio.Lock()
        self._attr_is_on = True

    async def _async_load_storage(self):
        """Load stored codes and flags from disk."""
        self._codes.update(await self._code_storage.async_load() or {})
        self._flags.update(await self._flag_storage.async_load() or {})
        self._storage_loaded = True

    def _extract_codes(self, commands, subdevice=None):
        """Extract a list of remote codes.
        If the command starts with 'b64:', extract the code from it.
        Otherwise use the command and optionally subdevice as keys to extract the
        actual command from storage.

        The commands are returned in sublists. For toggle commands, the sublist
        may contain two codes that must be sent alternately with each call."""
        code_list = []
        for cmd in commands:
            if cmd.startswith("b64:"):
                codes = [cmd[4:]]
            else:
                if subdevice is None:
                    raise ValueError("device must be specified")
                try:
                    codes = self._codes[subdevice][cmd]
                except KeyError as err:
                    raise ValueError(
                        f"Command {repr(cmd)} not found for {subdevice}"
                    ) from err
                if isinstance(codes, list):
                    codes = codes[:]
                else:
                    codes = [codes]

            for idx, code in enumerate(codes):
                try:
                    codes[idx] = code
                except ValueError as err:
                    raise ValueError(f"Invalid code: {repr(code)}") from err

            code_list.append(codes)
        return code_list

    def _encode_send_code(self, code, delay):
        """Encode a remote command into dps values to send."""
        # Based on https://github.com/jasonacox/tinytuya/issues/74 and
        # the docs it references, there are two kinds of IR devices.
        # 1. separate dps for control, code, study,...
        # 2. single dp (201) for send_ir, which takes JSON input,
        #    including control, code, delay, etc, and another for
        #    study_ir (202) that receives the codes in study mode.
        dps = {}
        if self._control_dp:
            # control and code are sent in seperate dps.
            dps = dps | self._control_dp.get_values_to_set(self._device, CMD_SEND)
            dps = dps | self._send_dp.get_values_to_set(self._device, code)
            if self._delay_dp:
                dps = dps | self._delay_dp.get_values_to_set(self._device, delay)
            if self._type_dp:
                dps = dps | self._type_dp.get_values_to_seet(self._device, 0)
        else:
            dps = dps | self._send_dp.get_values_to_set(
                self._device,
                json.dumps(
                    {
                        "control": CMD_SEND,
                        "head": "",
                        # leading zero means use head, any other leeading character is discarded.
                        "key1": "1" + code,
                        "type": 0,
                        "delay": int(delay),
                    }
                ),
            )

        return dps

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send remote commands"""
        kwargs[ATTR_COMMAND] = command
        kwargs = SERVICE_SEND_SCHEMA(kwargs)
        subdevice = kwargs.get(ATTR_DEVICE)
        repeat = kwargs.get(ATTR_NUM_REPEATS)
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS) * 1000
        service = f"{RM_DOMAIN}.{SERVICE_SEND_COMMAND}"
        if not self._storage_loaded:
            await self._async_load_storage()

        try:
            code_list = self._extract_codes(command, subdevice)
        except ValueError as err:
            _LOGGER.error("Failed to call %s: %s", service, err)
            raise

        at_least_one_sent = False
        for _, codes in product(range(repeat), code_list):
            if at_least_one_sent:
                await asyncio.sleep(delay)

            if len(codes) > 1:
                code = codes[self._flags[subdevice]]
            else:
                code = codes[0]

            dps_to_set = self._encode_send_code(code, delay)
            await self._device.async_set_properties(dps_to_set)

            if len(codes) > 1:
                self._flags[subdevice] ^= 1
            at_least_one_sent = True

        if at_least_one_sent:
            self._flag_storage.async_delay_save(self._flags, FLAG_SAVE_DELAY)

    async def async_learn_command(self, **kwargs: Any) -> None:
        """Learn a list of commands from a remote."""
        kwargs = SERVICE_LEARN_SCHEMA(kwargs)
        commands = kwargs[ATTR_COMMAND]
        subdevice = kwargs[ATTR_DEVICE]
        toggle = kwargs[ATTR_ALTERNATIVE]

        if not self._storage_loaded:
            await self._async_load_storage()

        async with self._lock:
            should_store = False

            for command in commands:
                code = await self._async_learn_command(command)
                _LOGGER.info("Learning %s for %s: %s", command, subdevice, code)
                # pulses = base64_to_pulses(code)
                # _LOGGER.debug("= pronto code: %s", pulses_to_pronto(pulses))
                # _LOGGER.debug("= width encoded: %s", pulses_to_width_encoded(pulses))
                if toggle:
                    code = [code, await self._async_learn_command(command)]
                self._codes.setdefault(subdevice, {}).update({command: code})
                should_store = True

            if should_store:
                await self._code_storage.async_save(self._codes)

    async def _async_learn_command(self, command):
        """Learn a single command"""
        service = f"{RM_DOMAIN}.{SERVICE_LEARN_COMMAND}"
        if self._control_dp:
            await self._control_dp.async_set_value(self._device, CMD_LEARN)
        else:
            await self._send_dp.async_set_value(
                self._device,
                json.dumps({"control": CMD_LEARN}),
            )

        persistent_notification.async_create(
            self._device._hass,
            f"Press the '{command}' button.",
            title="Learn command",
            notification_id="learn_command",
        )
        try:
            start_time = dt_util.utcnow()
            while (dt_util.utcnow() - start_time) < LEARNING_TIMEOUT:
                await asyncio.sleep(1)
                code = self._receive_dp.get_value(self._device)
                if code is not None:
                    return code
            _LOGGER.warning("Timed out without receiving code in %s", service)
            raise TimeoutError(
                f"No remote code received within {LEARNING_TIMEOUT.total_seconds()} seconds",
            )

        finally:
            persistent_notification.async_dismiss(
                self._device._hass, notification_id="learn_command"
            )
            if self._control_dp:
                await self._control_dp.async_set_value(
                    self._device,
                    CMD_ENDLEARN,
                )
            else:
                await self._send_dp.async_set_value(
                    self._device,
                    json.dumps({"control": CMD_ENDLEARN}),
                )

    async def async_delete_command(self, **kwargs: Any) -> None:
        """Delete a list of commands from a remote."""
        kwargs = SERVICE_DELETE_SCHEMA(kwargs)
        commands = kwargs[ATTR_COMMAND]
        subdevice = kwargs[ATTR_DEVICE]
        service = f"{RM_DOMAIN}.{SERVICE_DELETE_COMMAND}"

        if not self._storage_loaded:
            await self._async_load_storage()

        try:
            codes = self._codes[subdevice]
        except KeyError as err:
            err_msg = f"Device not found {repr(subdevice)}"
            _LOGGER.error("Failed to call %s. %s", service, err_msg)
            raise ValueError(err_msg) from err

        cmds_not_found = []
        for command in commands:
            try:
                del codes[command]
            except KeyError:
                cmds_not_found.append(command)

        if cmds_not_found:
            if len(cmds_not_found) == 1:
                err_msg = f"Command not found: {repr(cmds_not_found[0])}"
            else:
                err_msg = f"Commands not found: {repr(cmds_not_found)}"

            if len(cmds_not_found) == len(commands):
                _LOGGER.error("Failed to call %s. %s", service, err_msg)
                raise ValueError(err_msg)

            _LOGGER.error("Error during %s. %s", service, err_msg)

        # Clean up
        if not codes:
            del self._codes[subdevice]
            if self._flags.pop(subdevice, None) is not None:
                self._flag_storage.async_delay_save(self._flags, FLAG_SAVE_DELAY)
        self._code_storage.async_delay_save(self._codes, CODE_SAVE_DELAY)
