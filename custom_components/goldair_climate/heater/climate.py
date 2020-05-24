"""
Goldair WiFi Heater device.
"""
try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity

from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from ..device import GoldairTuyaDevice
from .const import (
    ATTR_ECO_TARGET_TEMPERATURE,
    ATTR_ERROR,
    ATTR_POWER_LEVEL,
    ATTR_POWER_MODE,
    ATTR_POWER_MODE_AUTO,
    ATTR_POWER_MODE_USER,
    ATTR_TARGET_TEMPERATURE,
    HVAC_MODE_TO_DPS_MODE,
    POWER_LEVEL_TO_DPS_LEVEL,
    PRESET_MODE_TO_DPS_MODE,
    PROPERTY_TO_DPS_ID,
    STATE_ANTI_FREEZE,
    STATE_COMFORT,
    STATE_ECO,
)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE


class GoldairHeater(ClimateEntity):
    """Representation of a Goldair WiFi heater."""

    def __init__(self, device):
        """Initialize the heater.
        Args:
            name (str): The device's name.
            device (GoldairTuyaDevice): The device API instance."""
        self._device = device

        self._support_flags = SUPPORT_FLAGS

        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {
            STATE_COMFORT: {"min": 5, "max": 35},
            STATE_ECO: {"min": 5, "max": 21},
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
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
    def unique_id(self):
        """Return the unique id for this heater."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this heater."""
        return self._device.device_info

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        hvac_mode = self.hvac_mode
        power_level = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL])
        if hvac_mode == HVAC_MODE_HEAT and power_level != "stop":
            return "mdi:radiator"
        else:
            return "mdi:radiator-disabled"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.preset_mode == STATE_COMFORT:
            return self._device.get_property(
                PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]
            )
        elif self.preset_mode == STATE_ECO:
            return self._device.get_property(
                PROPERTY_TO_DPS_ID[ATTR_ECO_TARGET_TEMPERATURE]
            )
        else:
            return None

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self.preset_mode and self.preset_mode != STATE_ANTI_FREEZE:
            return self._TEMPERATURE_LIMITS[self.preset_mode]["min"]
        else:
            return None

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self.preset_mode and self.preset_mode != STATE_ANTI_FREEZE:
            return self._TEMPERATURE_LIMITS[self.preset_mode]["max"]
        else:
            return None

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_PRESET_MODE) is not None:
            await self.async_set_preset_mode(kwargs.get(ATTR_PRESET_MODE))
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    async def async_set_target_temperature(self, target_temperature):
        target_temperature = int(round(target_temperature))
        preset_mode = self.preset_mode

        if preset_mode == STATE_ANTI_FREEZE:
            raise ValueError("You cannot set the temperature in Anti-freeze mode.")

        limits = self._TEMPERATURE_LIMITS[preset_mode]
        if not limits["min"] <= target_temperature <= limits["max"]:
            raise ValueError(
                f"Target temperature ({target_temperature}) must be between "
                f'{limits["min"]} and {limits["max"]}'
            )

        if preset_mode == STATE_COMFORT:
            await self._device.async_set_property(
                PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE], target_temperature
            )
        elif preset_mode == STATE_ECO:
            await self._device.async_set_property(
                PROPERTY_TO_DPS_ID[ATTR_ECO_TARGET_TEMPERATURE], target_temperature
            )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE])

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])

        if dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(HVAC_MODE_TO_DPS_MODE, dps_mode)
        else:
            return STATE_UNAVAILABLE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return list(HVAC_MODE_TO_DPS_MODE.keys())

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = HVAC_MODE_TO_DPS_MODE[hvac_mode]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode
        )

    @property
    def preset_mode(self):
        """Return current preset mode, ie Comfort, Eco, Anti-freeze."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE])
        if dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(
                PRESET_MODE_TO_DPS_MODE, dps_mode
            )
        else:
            return None

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return list(PRESET_MODE_TO_DPS_MODE.keys())

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        dps_mode = PRESET_MODE_TO_DPS_MODE[preset_mode]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE], dps_mode
        )

    @property
    def swing_mode(self):
        """Return the power level."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_POWER_MODE])
        if dps_mode == ATTR_POWER_MODE_USER:
            dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL])
        return GoldairTuyaDevice.get_key_for_value(POWER_LEVEL_TO_DPS_LEVEL, dps_mode)

    @property
    def swing_modes(self):
        """List of power levels."""
        return list(POWER_LEVEL_TO_DPS_LEVEL.keys())

    async def async_set_swing_mode(self, swing_mode):
        """Set new power level."""
        new_level = swing_mode
        if new_level not in POWER_LEVEL_TO_DPS_LEVEL.keys():
            raise ValueError(f"Invalid power level: {new_level}")
        dps_level = POWER_LEVEL_TO_DPS_LEVEL[new_level]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL], dps_level
        )

    @property
    def device_state_attributes(self):
        """Get additional attributes that HA doesn't naturally support."""
        error = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ERROR])

        return {ATTR_ERROR: error or None}

    async def async_update(self):
        await self._device.async_refresh()
