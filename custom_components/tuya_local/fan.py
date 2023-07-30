"""
Setup for different kinds of Tuya fan devices
"""
import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "fan",
        TuyaLocalFan,
    )


class TuyaLocalFan(TuyaLocalEntity, FanEntity):
    """Representation of a Tuya Fan entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the fan device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._switch_dps = dps_map.pop("switch", None)
        self._preset_dps = dps_map.pop("preset_mode", None)
        self._speed_dps = dps_map.pop("speed", None)
        self._oscillate_dps = dps_map.pop("oscillate", None)
        self._direction_dps = dps_map.pop("direction", None)
        self._init_end(dps_map)

        self._support_flags = 0
        if self._preset_dps:
            self._support_flags |= FanEntityFeature.PRESET_MODE
        if self._speed_dps:
            self._support_flags |= FanEntityFeature.SET_SPEED
        if self._oscillate_dps:
            self._support_flags |= FanEntityFeature.OSCILLATE
        if self._direction_dps:
            self._support_flags |= FanEntityFeature.DIRECTION

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def is_on(self):
        """Return whether the switch is on or not."""
        # If there is no switch, it is always on
        if self._switch_dps is None:
            return self.available
        return self._switch_dps.get_value(self._device)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        if self._switch_dps is None:
            raise NotImplementedError()
        await self._switch_dps.async_set_value(self._device, True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        if self._switch_dps is None:
            raise NotImplementedError
        await self._switch_dps.async_set_value(self._device, False)

    @property
    def percentage(self):
        """Return the currently set percentage."""
        if self._speed_dps is None:
            return None
        return self._speed_dps.get_value(self._device)

    @property
    def percentage_step(self):
        """Return the step for percentage."""
        if self._speed_dps is None:
            return None
        if self._speed_dps.values(self._device):
            return 100 / len(self._speed_dps.values(self._device))
        return self._speed_dps.step(self._device)

    @property
    def speed_count(self):
        """Return the number of speeds supported by the fan."""
        if self._speed_dps is None:
            return 0
        if self._speed_dps.values(self._device):
            return len(self._speed_dps.values(self._device))
        return int(round(100 / self.percentage_step))

    async def async_set_percentage(self, percentage):
        """Set the fan speed as a percentage."""
        # If speed is 0, turn the fan off
        if percentage == 0 and self._switch_dps:
            return await self.async_turn_off()

        if self._speed_dps is None:
            return None
        # If there is a fixed list of values, snap to the closest one
        if self._speed_dps.values(self._device):
            percentage = min(
                self._speed_dps.values(self._device),
                key=lambda x: abs(x - percentage),
            )

        values_to_set = self._speed_dps.get_values_to_set(self._device, percentage)
        if not self.is_on and self._switch_dps:
            values_to_set.update(self._switch_dps.get_values_to_set(self._device, True))

        await self._device.async_set_properties(values_to_set)

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self._preset_dps is None:
            return None
        return self._preset_dps.get_value(self._device)

    @property
    def preset_modes(self):
        """Return the list of presets that this device supports."""
        if self._preset_dps is None:
            return []
        return self._preset_dps.values(self._device)

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""
        if self._preset_dps is None:
            raise NotImplementedError()
        await self._preset_dps.async_set_value(self._device, preset_mode)

    @property
    def current_direction(self):
        """Return the current direction [forward or reverse]."""
        if self._direction_dps is None:
            return None
        return self._direction_dps.get_value(self._device)

    async def async_set_direction(self, direction):
        """Set the direction of the fan."""
        if self._direction_dps is None:
            raise NotImplementedError()
        await self._direction_dps.async_set_value(self._device, direction)

    @property
    def oscillating(self):
        """Return whether or not the fan is oscillating."""
        if self._oscillate_dps is None:
            return None
        return self._oscillate_dps.get_value(self._device)

    async def async_oscillate(self, oscillating):
        """Oscillate the fan."""
        if self._oscillate_dps is None:
            raise NotImplementedError()
        await self._oscillate_dps.async_set_value(self._device, oscillating)
