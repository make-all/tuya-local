"""
Platform to control tuya climate devices.
"""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_HUMIDITY,
    DEFAULT_MIN_TEMP,
    HVAC_MODE_AUTO,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TEMP_KELVIN,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


class TuyaLocalClimate(ClimateEntity):
    """Representation of a Tuya Climate entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the climate device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        self._device = device
        self._config = config
        self._support_flags = 0
        self._current_temperature_dps = None
        self._temperature_dps = None
        self._temp_high_dps = None
        self._temp_low_dps = None
        self._current_humidity_dps = None
        self._humidity_dps = None
        self._preset_mode_dps = None
        self._swing_mode_dps = None
        self._fan_mode_dps = None
        self._hvac_mode_dps = None
        self._unit_dps = None
        self._attr_dps = []

        for d in config.dps():
            if d.name == "hvac_mode":
                self._hvac_mode_dps = d
            elif d.name == ATTR_TEMPERATURE:
                self._temperature_dps = d
            elif d.name == ATTR_TARGET_TEMP_HIGH:
                self._temp_high_dps = d
            elif d.name == ATTR_TARGET_TEMP_LOW:
                self._temp_low_dps = d
            elif d.name == ATTR_CURRENT_TEMPERATURE:
                self._current_temperature_dps = d
            elif d.name == ATTR_HUMIDITY:
                self._humidity_dps = d
                self._support_flags |= SUPPORT_TARGET_HUMIDITY
            elif d.name == ATTR_CURRENT_HUMIDITY:
                self._current_humidity_dps = d
            elif d.name == ATTR_PRESET_MODE:
                self._preset_mode_dps = d
                self._support_flags |= SUPPORT_PRESET_MODE
            elif d.name == ATTR_SWING_MODE:
                self._swing_mode_dps = d
                self._support_flags |= SUPPORT_SWING_MODE
            elif d.name == ATTR_FAN_MODE:
                self._fan_mode_dps = d
                self._support_flags |= SUPPORT_FAN_MODE
            elif d.name == "temperature_unit":
                self._unit_dps = d
            elif not d.hidden:
                self._attr_dps.append(d)

        if self._temp_high_dps is not None and self._temp_low_dps is not None:
            self._support_flags |= SUPPORT_TARGET_TEMPERATURE_RANGE
        elif self._temperature_dps is not None:
            self._support_flags |= SUPPORT_TARGET_TEMPERATURE

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
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.hvac_mode == HVAC_MODE_OFF:
            return "mdi:hvac-off"
        else:
            return "mdi:hvac"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._unit_dps is not None:
            unit = self._unit_dps.get_value(self._device)
            # Only return valid units
            if unit == "C":
                return TEMP_CELSIUS
            elif unit == "F":
                return TEMP_FAHRENHEIT
            elif unit == "K":
                return TEMP_KELVIN
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the currently set target temperature."""
        if self._temperature_dps is None:
            raise NotImplementedError()
        return self._temperature_dps.get_value(self._device)

    @property
    def target_temperature_high(self):
        """Return the currently set high target temperature."""
        if self._temp_high_dps is None:
            raise NotImplementedError()
        return self._temp_high_dps.get_value(self._device)

    @property
    def target_temperature_low(self):
        """Return the currently set low target temperature."""
        if self._temp_low_dps is None:
            raise NotImplementedError()
        return self._temp_low_dps.get_value(self._device)

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        dps = self._temperature_dps
        if dps is None:
            dps = self._temp_high_dps
        if dps is None:
            dps = self._temp_low_dps
        if dps is None:
            return 1
        return dps.step(self._device)

    @property
    def min_temp(self):
        """Return the minimum supported target temperature."""
        if self._temperature_dps is None:
            return None
        if self._temperature_dps.range is None:
            return DEFAULT_MIN_TEMP
        return self._temperature_dps.range["min"]

    @property
    def max_temp(self):
        """Return the maximum supported target temperature."""
        if self._temperature_dps is None:
            return None
        if self._temperature_dps.range is None:
            return DEFAULT_MAX_TEMP
        return self._temperature_dps.range["max"]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_PRESET_MODE) is not None:
            await self.async_set_preset_mode(kwargs.get(ATTR_PRESET_MODE))
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))
        high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        if high is not None or low is not None:
            await self.async_set_target_temperature_range(low, high)

    async def async_set_target_temperature(self, target_temperature):
        if self._temperature_dps is None:
            raise NotImplementedError()

        await self._temperature_dps.async_set_value(self._device, target_temperature)

    async def async_set_target_temperature_range(self, low, high):
        """Set the target temperature range."""
        dps_map = {}
        if low is not None and self._temp_low_dps is not None:
            dps_map.update(self._temp_low_dps.get_values_to_set(self._device, low))
        if high is not None and self._temp_high_dps is not None:
            dps_map.update(self._temp_high_dps.get_values_to_set(self._device, high))
        if dps_map:
            await self._device.async_set_properties(dps_map)

    @property
    def current_temperature(self):
        """Return the current measured temperature."""
        if self._current_temperature_dps is None:
            return None
        return self._current_temperature_dps.get_value(self._device)

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

    async def async_set_humidity(self, target_humidity):
        if self._humidity_dps is None:
            raise NotImplementedError()

        await self._humidity_dps.async_set_value(self._device, target_humidity)

    @property
    def current_humidity(self):
        """Return the current measured humidity."""
        if self._current_humidity_dps is None:
            return None
        return self._current_humidity_dps.get_value(self._device)

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        if self._hvac_mode_dps is None:
            return HVAC_MODE_AUTO
        hvac_mode = self._hvac_mode_dps.get_value(self._device)
        return STATE_UNAVAILABLE if hvac_mode is None else hvac_mode

    @property
    def hvac_modes(self):
        """Return available HVAC modes."""
        if self._hvac_mode_dps is None:
            return []
        else:
            return self._hvac_mode_dps.values

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        if self._hvac_mode_dps is None:
            raise NotImplementedError()
        await self._hvac_mode_dps.async_set_value(self._device, hvac_mode)

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self._preset_mode_dps is None:
            raise NotImplementedError()
        return self._preset_mode_dps.get_value(self._device)

    @property
    def preset_modes(self):
        """Return the list of presets that this device supports."""
        if self._preset_mode_dps is None:
            return None
        return self._preset_mode_dps.values

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""
        if self._preset_mode_dps is None:
            raise NotImplementedError()
        await self._preset_mode_dps.async_set_value(self._device, preset_mode)

    @property
    def swing_mode(self):
        """Return the current swing mode."""
        if self._swing_mode_dps is None:
            raise NotImplementedError()
        return self._swing_mode_dps.get_value(self._device)

    @property
    def swing_modes(self):
        """Return the list of swing modes that this device supports."""
        if self._swing_mode_dps is None:
            return None
        return self._swing_mode_dps.values

    async def async_set_swing_mode(self, swing_mode):
        """Set the preset mode."""
        if self._swing_mode_dps is None:
            raise NotImplementedError()
        await self._swing_mode_dps.async_set_value(self._device, swing_mode)

    @property
    def fan_mode(self):
        """Return the current swing mode."""
        if self._fan_mode_dps is None:
            raise NotImplementedError()
        return self._fan_mode_dps.get_value(self._device)

    @property
    def fan_modes(self):
        """Return the list of swing modes that this device supports."""
        if self._fan_mode_dps is None:
            return None
        return self._fan_mode_dps.values

    async def async_set_fan_mode(self, fan_mode):
        """Set the preset mode."""
        if self._fan_mode_dps is None:
            raise NotImplementedError()
        await self._fan_mode_dps.async_set_value(self._device, fan_mode)

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_update(self):
        await self._device.async_refresh()
