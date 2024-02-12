"""
Setup for different kinds of Tuya climate devices
"""
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import (
    ATTR_AUX_HEAT,
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_HUMIDITY,
    DEFAULT_MIN_TEMP,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    UnitOfTemperature,
)

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity, unit_from_ascii

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "climate",
        TuyaLocalClimate,
    )


def validate_temp_unit(unit):
    unit = unit_from_ascii(unit)
    try:
        return UnitOfTemperature(unit)
    except ValueError:
        return None


class TuyaLocalClimate(TuyaLocalEntity, ClimateEntity):
    """Representation of a Tuya Climate entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the climate device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)

        self._aux_heat_dps = dps_map.pop(ATTR_AUX_HEAT, None)
        self._current_temperature_dps = dps_map.pop(
            ATTR_CURRENT_TEMPERATURE,
            None,
        )
        self._current_humidity_dps = dps_map.pop(ATTR_CURRENT_HUMIDITY, None)
        self._fan_mode_dps = dps_map.pop(ATTR_FAN_MODE, None)
        self._humidity_dps = dps_map.pop(ATTR_HUMIDITY, None)
        self._hvac_mode_dps = dps_map.pop(ATTR_HVAC_MODE, None)
        self._hvac_action_dps = dps_map.pop(ATTR_HVAC_ACTION, None)
        self._preset_mode_dps = dps_map.pop(ATTR_PRESET_MODE, None)
        self._swing_mode_dps = dps_map.pop(ATTR_SWING_MODE, None)
        self._temperature_dps = dps_map.pop(ATTR_TEMPERATURE, None)
        self._temp_high_dps = dps_map.pop(ATTR_TARGET_TEMP_HIGH, None)
        self._temp_low_dps = dps_map.pop(ATTR_TARGET_TEMP_LOW, None)
        self._unit_dps = dps_map.pop("temperature_unit", None)
        self._mintemp_dps = dps_map.pop("min_temperature", None)
        self._maxtemp_dps = dps_map.pop("max_temperature", None)

        self._init_end(dps_map)
        self._support_flags = ClimateEntityFeature(0)

        if self._aux_heat_dps:
            self._support_flags |= ClimateEntityFeature.AUX_HEAT
        if self._fan_mode_dps:
            self._support_flags |= ClimateEntityFeature.FAN_MODE
        if self._humidity_dps:
            self._support_flags |= ClimateEntityFeature.TARGET_HUMIDITY
        if self._preset_mode_dps:
            self._support_flags |= ClimateEntityFeature.PRESET_MODE
        if self._swing_mode_dps:
            self._support_flags |= ClimateEntityFeature.SWING_MODE

        if self._temp_high_dps and self._temp_low_dps:
            self._support_flags |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        elif self._temperature_dps is not None:
            self._support_flags |= ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # If there is a separate DPS that returns the units, use that
        if self._unit_dps is not None:
            unit = validate_temp_unit(self._unit_dps.get_value(self._device))
            # Only return valid units
            if unit is not None:
                return unit
        # If there unit attribute configured in the temperature dps, use that
        if self._temperature_dps:
            unit = validate_temp_unit(self._temperature_dps.unit)
            if unit is not None:
                return unit
        if self._temp_high_dps:
            unit = validate_temp_unit(self._temp_high_dps.unit)
            if unit is not None:
                return unit
        if self._temp_low_dps:
            unit = validate_temp_unit(self._temp_low_dps.unit)
            if unit is not None:
                return unit
        if self._current_temperature_dps:
            unit = validate_temp_unit(self._current_temperature_dps.unit)
            if unit is not None:
                return unit
        # Return the default unit
        return UnitOfTemperature.CELSIUS

    @property
    def precision(self):
        """Return the precision of the temperature setting."""
        # unlike sensor, this is a decimal of the smallest unit that can be
        # represented, not a number of decimal places.
        dp = self._temperature_dps or self._temp_high_dps
        temp = dp.scale(self._device) if dp else 1
        current = (
            self._current_temperature_dps.scale(self._device)
            if self._current_temperature_dps
            else 1
        )
        if max(temp, current) > 1.0:
            return PRECISION_TENTHS
        return PRECISION_WHOLE

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
        # if a separate min_temperature dps is specified, the device tells us.
        if self._mintemp_dps is not None:
            min = self._mintemp_dps.get_value(self._device)
            if min is not None:
                return min

        if self._temperature_dps is None:
            if self._temp_low_dps is None:
                return None
            r = self._temp_low_dps.range(self._device)
        else:
            r = self._temperature_dps.range(self._device)
        return DEFAULT_MIN_TEMP if r is None else r[0]

    @property
    def max_temp(self):
        """Return the maximum supported target temperature."""
        # if a separate max_temperature dps is specified, the device tells us.
        if self._maxtemp_dps is not None:
            max = self._maxtemp_dps.get_value(self._device)
            if max is not None:
                return max

        if self._temperature_dps is None:
            if self._temp_high_dps is None:
                return None
            r = self._temp_high_dps.range(self._device)
        else:
            r = self._temperature_dps.range(self._device)
        return DEFAULT_MAX_TEMP if r is None else r[1]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_PRESET_MODE) is not None:
            await self.async_set_preset_mode(kwargs.get(ATTR_PRESET_MODE))
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(
                kwargs.get(ATTR_TEMPERATURE),
            )
        high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        if high is not None or low is not None:
            await self.async_set_target_temperature_range(low, high)

    async def async_set_target_temperature(self, target_temperature):
        if self._temperature_dps is None:
            raise NotImplementedError()

        await self._temperature_dps.async_set_value(
            self._device,
            target_temperature,
        )

    async def async_set_target_temperature_range(self, low, high):
        """Set the target temperature range."""
        dps_map = {}
        if low is not None and self._temp_low_dps is not None:
            dps_map.update(
                self._temp_low_dps.get_values_to_set(self._device, low),
            )
        if high is not None and self._temp_high_dps is not None:
            dps_map.update(
                self._temp_high_dps.get_values_to_set(self._device, high),
            )
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
        r = self._humidity_dps.range(self._device)
        return DEFAULT_MIN_HUMIDITY if r is None else r[0]

    @property
    def max_humidity(self):
        """Return the maximum supported target humidity."""
        if self._humidity_dps is None:
            return None
        r = self._humidity_dps.range(self._device)
        return DEFAULT_MAX_HUMIDITY if r is None else r[1]

    async def async_set_humidity(self, humidity: int):
        if self._humidity_dps is None:
            raise NotImplementedError()

        await self._humidity_dps.async_set_value(self._device, humidity)

    @property
    def current_humidity(self):
        """Return the current measured humidity."""
        if self._current_humidity_dps is None:
            return None
        return self._current_humidity_dps.get_value(self._device)

    @property
    def hvac_action(self):
        """Return the current HVAC action."""
        if self._hvac_action_dps is None:
            return None
        action = self._hvac_action_dps.get_value(self._device)
        try:
            return HVACAction(action) if action else None
        except ValueError:
            _LOGGER.warning(
                "%s/%s: Unrecognised HVAC Action %s ignored",
                self._config._device.config,
                self.name or "climate",
                action,
            )
            return None

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        if self._hvac_mode_dps is None:
            return HVACMode.AUTO
        hvac_mode = self._hvac_mode_dps.get_value(self._device)
        try:
            return HVACMode(hvac_mode) if hvac_mode else None
        except ValueError:
            _LOGGER.warning(
                "%s/%s: Unrecognised HVAC Mode of %s ignored",
                self._config._device.config,
                self.name or "climate",
                hvac_mode,
            )
            return None

    @property
    def hvac_modes(self):
        """Return available HVAC modes."""
        if self._hvac_mode_dps is None:
            return [HVACMode.AUTO]
        else:
            return self._hvac_mode_dps.values(self._device)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        if self._hvac_mode_dps is None:
            raise NotImplementedError()
        await self._hvac_mode_dps.async_set_value(self._device, hvac_mode)

    async def async_turn_on(self):
        """Turn on the climate device."""
        # Bypass the usual dps mapping to switch the power dp directly
        # this way the hvac_mode will be kept when toggling off and on.
        if self._hvac_mode_dps and self._hvac_mode_dps.type is bool:
            await self._device.async_set_property(self._hvac_mode_dps.id, True)
        else:
            await super().async_turn_on()

    async def async_turn_off(self):
        """Turn off the climate device."""
        # Bypass the usual dps mapping to switch the power dp directly
        # this way the hvac_mode will be kept when toggling off and on.
        if self._hvac_mode_dps and self._hvac_mode_dps.type is bool:
            await self._device.async_set_property(
                self._hvac_mode_dps.id,
                False,
            )
        else:
            await super().async_turn_off()

    @property
    def is_aux_heat(self):
        """Return state of aux heater"""
        if self._aux_heat_dps is None:
            return None
        else:
            return self._aux_heat_dps.get_value(self._device)

    async def async_turn_aux_heat_on(self):
        """Turn on aux heater."""
        if self._aux_heat_dps is None:
            raise NotImplementedError()
        await self._aux_heat_dps.async_set_value(self._device, True)

    async def async_turn_aux_heat_off(self):
        """Turn off aux heater."""
        if self._aux_heat_dps is None:
            raise NotImplementedError()
        await self._aux_heat_dps.async_set_value(self._device, False)

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
        return self._preset_mode_dps.values(self._device)

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
        return self._swing_mode_dps.values(self._device)

    async def async_set_swing_mode(self, swing_mode):
        """Set the preset mode."""
        if self._swing_mode_dps is None:
            raise NotImplementedError()
        await self._swing_mode_dps.async_set_value(self._device, swing_mode)

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        if self._fan_mode_dps is None:
            raise NotImplementedError()
        return self._fan_mode_dps.get_value(self._device)

    @property
    def fan_modes(self):
        """Return the list of fan modes that this device supports."""
        if self._fan_mode_dps is None:
            return None
        return self._fan_mode_dps.values(self._device)

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        if self._fan_mode_dps is None:
            raise NotImplementedError()
        await self._fan_mode_dps.async_set_value(self._device, fan_mode)
