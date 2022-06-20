"""
Platform to control tuya humidifier and dehumidifier devices.
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

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


class TuyaLocalHumidifier(TuyaLocalEntity, HumidifierEntity):
    """Representation of a Tuya Humidifier entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the humidifier device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        dps_map = self._init_begin(device, config)
        self._humidity_dps = dps_map.pop("humidity", None)
        self._mode_dps = dps_map.pop("mode", None)
        self._switch_dps = dps_map.pop("switch", None)
        self._init_end(dps_map)

        self._support_flags = 0
        if self._mode_dps:
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
        if self._switch_dps is None:
            return self.available
        return self._switch_dps.get_value(self._device)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._switch_dps.async_set_value(self._device, True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._switch_dps.async_set_value(self._device, False)

    @property
    def target_humidity(self):
        """Return the currently set target humidity."""
        if self._humidity_dps is None:
            raise NotImplementedError()
        return self._humidity_dps.get_value(self._device)

    @property
    def min_humidity(self):
        """Return the minimum supported target humidity."""
        if self._humidity_dps is None:
            return None
        r = self._humidity_dps.range(self._device)
        return DEFAULT_MIN_HUMIDITY if r is None else r["min"]

    @property
    def max_humidity(self):
        """Return the maximum supported target humidity."""
        if self._humidity_dps is None:
            return None
        r = self._humidity_dps.range(self._device)
        return DEFAULT_MAX_HUMIDITY if r is None else r["max"]

    async def async_set_humidity(self, humidity):
        if self._humidity_dps is None:
            raise NotImplementedError()

        await self._humidity_dps.async_set_value(self._device, humidity)

    @property
    def mode(self):
        """Return the current preset mode."""
        if self._mode_dps is None:
            raise NotImplementedError()
        return self._mode_dps.get_value(self._device)

    @property
    def available_modes(self):
        """Return the list of presets that this device supports."""
        if self._mode_dps is None:
            return None
        return self._mode_dps.values(self._device)

    async def async_set_mode(self, mode):
        """Set the preset mode."""
        if self._mode_dps is None:
            raise NotImplementedError()
        await self._mode_dps.async_set_value(self._device, mode)
