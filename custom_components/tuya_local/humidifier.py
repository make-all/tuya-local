"""
Setup for different kinds of Tuya humidifier devices
"""
import logging

from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.components.humidifier.const import (
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MIN_HUMIDITY,
)

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
        "humidifier",
        TuyaLocalHumidifier,
    )


class TuyaLocalHumidifier(TuyaLocalEntity, HumidifierEntity):
    """Representation of a Tuya Humidifier entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the humidifier device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._current_humidity_dp = dps_map.pop("current_humidity", None)
        self._humidity_dp = dps_map.pop("humidity", None)
        self._mode_dp = dps_map.pop("mode", None)
        self._switch_dp = dps_map.pop("switch", None)
        self._init_end(dps_map)

        self._support_flags = HumidifierEntityFeature(0)
        if self._mode_dp:
            self._support_flags |= HumidifierEntityFeature.MODES

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def device_class(self):
        """Return the class of this device"""
        return (
            HumidifierDeviceClass.DEHUMIDIFIER
            if self._config.device_class == "dehumidifier"
            else HumidifierDeviceClass.HUMIDIFIER
        )

    @property
    def is_on(self):
        """Return whether the switch is on or not."""
        # If there is no switch, it is always on if available
        if self._switch_dp is None:
            return self.available
        return self._switch_dp.get_value(self._device)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._switch_dp.async_set_value(self._device, True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._switch_dp.async_set_value(self._device, False)

    @property
    def current_humidity(self):
        """Return the current humidity if available."""
        if self._current_humidity_dp:
            return self._current_humidity_dp.get_value(self._device)

    @property
    def target_humidity(self):
        """Return the currently set target humidity."""
        if self._humidity_dp is None:
            raise NotImplementedError()
        return self._humidity_dp.get_value(self._device)

    @property
    def min_humidity(self):
        """Return the minimum supported target humidity."""
        if self._humidity_dp is None:
            return None
        r = self._humidity_dp.range(self._device)
        return DEFAULT_MIN_HUMIDITY if r is None else r[0]

    @property
    def max_humidity(self):
        """Return the maximum supported target humidity."""
        if self._humidity_dp is None:
            return None
        r = self._humidity_dp.range(self._device)
        return DEFAULT_MAX_HUMIDITY if r is None else r[1]

    async def async_set_humidity(self, humidity):
        if self._humidity_dp is None:
            raise NotImplementedError()

        await self._humidity_dp.async_set_value(self._device, humidity)

    @property
    def mode(self):
        """Return the current preset mode."""
        if self._mode_dp is None:
            raise NotImplementedError()
        return self._mode_dp.get_value(self._device)

    @property
    def available_modes(self):
        """Return the list of presets that this device supports."""
        if self._mode_dp is None:
            return None
        return self._mode_dp.values(self._device)

    async def async_set_mode(self, mode):
        """Set the preset mode."""
        if self._mode_dp is None:
            raise NotImplementedError()
        await self._mode_dp.async_set_value(self._device, mode)
