"""
Implementation of Tuya infrared control devices
"""

import asyncio
import json
import logging

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
        timings = command.get_raw_timings()
        split = {}
        raw = []
        i = 0
        for timing in timings:
            if timing.high_us > 50000:
                split[i] = timing.high_us - 5000
                raw.append(5000)
                raw.append(timing.low_us)
            elif timing.low_us > 50000:
                raw.append(timing.high_us)
                raw.append(5000)
                split[i + 2] = timing.low_us - 5000
            else:
                raw.append(timing.high_us)
                raw.append(timing.low_us)
            i += 2

        # HA's converter leaves the last low timing as 0, but Tuya seems to expect around 5 - 10 ms
        if raw[-1] == 0:
            raw[-1] = 5000

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
