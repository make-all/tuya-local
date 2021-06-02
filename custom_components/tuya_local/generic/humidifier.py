"""
Platform to control tuya humidifier and dehumidifier devices.
"""
import logging

from homeassistant.components.humidifier import HumidifierEntity
from homeassistant.components.humidifier.const import (
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MIN_HUMIDITY,
    DEVICE_CLASS_DEHUMIDIFIER,
    DEVICE_CLASS_HUMIDIFIER,
    SUPPORT_MODES,
)
from homeassistant.const import (
    STATE_UNAVAILABLE,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


class TuyaLocalHumidifier(HumidifierEntity):
    """Representation of a Tuya Humidifier entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the humidifier device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        self._device = device
        self._config = config
        self._support_flags = 0
        self._humidity_dps = None
        self._mode_dps = None
        self._switch_dps = None
        self._attr_dps = []
        for d in config.dps():
            if d.name == "switch":
                self._switch_dps = d
            elif d.name == "humidity":
                self._humidity_dps = d
            elif d.name == "mode":
                self._mode_dps = d
                self._support_flags |= SUPPORT_MODES
            elif not d.hidden:
                self._attr_dps.append(d)

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._device.name

    @property
    def friendly_name(self):
        """Return the friendly name of the climate entity for the UI."""
        return self._config.name

    @property
    def unique_id(self):
        """Return the unique id for this climate device."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this heater."""
        return self._device.device_info

    @property
    def device_class(self):
        """Return the class of this device"""
        return (
            DEVICE_CLASS_DEHUMIDIFIER
            if self._config.device_class == "dehumidifier"
            else DEVICE_CLASS_HUMIDIFIER
        )

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:air-humidifier"
        else:
            return "mdi:air-humidifier-off"

    @property
    def is_on(self):
        """Return whether the switch is on or not."""
        is_switched_on = self._switch_dps.get_value(self._device)

        if is_switched_on is None:
            return STATE_UNAVAILABLE
        else:
            return is_switched_on

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
        if self._humidity_dps.range is None:
            return DEFAULT_MIN_HUMIDITY
        return self._humidity_dps.range["min"]

    @property
    def max_humidity(self):
        """Return the maximum supported target humidity."""
        if self._humidity_dps is None:
            return None
        if self._humidity_dps.range is None:
            return DEFAULT_MAX_HUMIDITY
        return self._humidity_dps.range["max"]

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
        return self._mode_dps.values

    async def async_set_mode(self, mode):
        """Set the preset mode."""
        if self._mode_dps is None:
            raise NotImplementedError()
        await self._mode_dps.async_set_value(self._device, mode)

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_update(self):
        await self._device.async_refresh()
