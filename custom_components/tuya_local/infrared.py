"""
Implementation of Tuya infrared control devices
"""

import asyncio
import json
import logging
from typing import override

from homeassistant.components.infrared import InfraredCommand, InfraredEntity
from tinytuya.Contrib.IRRemoteControlDevice import IRRemoteControlDevice as IR

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Tuya Local infrared control platform."""
    config = {**entry.data, **entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "infrared",
        TuyaLocalInfrared,
    )


class TuyaLocalInfrared(TuyaLocalEntity, InfraredEntity):
    """Representation of a Tuya Local infrared control device."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """Initialize the infrared control device."""
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._send_dp = dps_map.pop("send", None)
        self._command_dp = dps_map.pop("control", None)
        self._type_dp = dps_map.pop("code_type", None)
        self._init_end(dps_map)

    async def async_send_command(self, command: InfraredCommand) -> None:
        """Handle sending an infrared command."""
        if isinstance(command, TuyaRemoteCommand):
            # If it's already a TuyaRemoteCommand, skip the round-trip conversion
            tuya_command = command.code
            _LOGGER.info("%s sending command: %s", self._config.config_id, tuya_command)
            await self._ir_send(tuya_command)
            return

        timings = command.get_raw_timings()
        split = {}
        raw = []
        i = 0
        for timing in timings:
            utiming = abs(timing)
            if utiming > 50000:
                split[i] = utiming - 5000
                raw.append(5000)
            else:
                raw.append(utiming)
            i += 1

        # HA format leaves off the last low timing, but Tuya needs it
        if len(raw) % 2 == 1:
            raw.append(5000)

        start = 0
        for s, t in split.items():
            tuya_command = IR.pulses_to_base64(raw[start:s])
            _LOGGER.info("%s sending command: %s", self._config.config_id, tuya_command)
            start = s
            await self._ir_send(tuya_command)
            await asyncio.sleep(t / 1000000.0)
        if start < len(raw):
            tuya_command = IR.pulses_to_base64(raw[start:])
            _LOGGER.info("%s sending command: %s", self._config.config_id, tuya_command)
            await self._ir_send(tuya_command)

    async def _ir_send(self, tuya_command: str):
        """Send the infrared command to the device."""
        if self._send_dp:
            if self._command_dp:
                await self._device.async_set_properties(
                    self._package_multi_dp_send(tuya_command)
                )
            else:
                await self._send_dp.async_set_value(
                    self._device,
                    self._package_single_dp_send(tuya_command),
                )

    def _package_single_dp_send(self, command: str) -> str:
        """Package the command for a single DP (usually dp id 201) send."""
        json_command = {
            "control": "send_ir",
            "type": 0,
            "head": "",
            "key1": "1" + command,
        }
        return json.dumps(json_command)

    def _package_multi_dp_send(self, command: str) -> dict:
        """Package the command for a multi DP send"""
        return {
            f"{self._command_dp.id}": "send_ir",
            f"{self._type_dp.id}": 0,
            f"{self._send_dp.id}": command,
        }


# Used to send legacy remote learned commands via infrared entities.
# This allows the learned commands to be sent via infrared entities
# provided by other integrations.
class TuyaRemoteCommand(InfraredCommand):
    """Representation of a command in Tuya uncompressed format."""

    def __init__(self, *, code: str):
        super().__init__(modulation=38000, repeat_count=0)
        self.code = code

    @override
    def get_raw_timings(self) -> list[int]:
        """Get the raw timings for the command."""
        # The code is expected to be an uncompressed Tuya IR code
        try:
            pulses = IR.base64_to_pulses(self.code)
            even = True
            return [p * -1 if (even := not even) else p for p in pulses]
        except ValueError as err:
            raise ValueError(f"Invalid code format: {repr(self.code)}") from err
