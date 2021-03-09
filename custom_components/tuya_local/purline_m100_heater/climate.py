"""
Purline Hoti M100 WiFi Heater device.
"""
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_SWING_MODE,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from ..device import TuyaLocalDevice
from .const import (
    ATTR_POWER_LEVEL,
    ATTR_TARGET_TEMPERATURE,
    POWER_LEVEL_AUTO,
    POWER_LEVEL_FANONLY,
    POWER_LEVEL_TO_DPS_LEVEL,
    PRESET_AUTO,
    PRESET_FAN,
    PROPERTY_TO_DPS_ID,
)

SUPPORT_FLAGS = SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE | SUPPORT_TARGET_TEMPERATURE


class PurlineM100Heater(ClimateEntity):
    """Representation of a Purline Hoti M100 WiFi heater."""

    def __init__(self, device):
        """Initialize the heater.
        Args:
            device (TuyaLocalDevice): The device API instance."""
        self._device = device

        self._support_flags = SUPPORT_FLAGS

        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {"min": 15, "max": 35}

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

        if hvac_mode == HVAC_MODE_HEAT:
            return "mdi:radiator"
        elif hvac_mode == HVAC_MODE_FAN_ONLY:
            return "mdi:fan"
        else:
            return "mdi:radiator-disabled"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE])

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._TEMPERATURE_LIMITS["min"]

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._TEMPERATURE_LIMITS["max"]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    async def async_set_target_temperature(self, target_temperature):
        target_temperature = int(round(target_temperature))

        limits = self._TEMPERATURE_LIMITS
        if not limits["min"] <= target_temperature <= limits["max"]:
            raise ValueError(
                f"Target temperature ({target_temperature}) must be between "
                f'{limits["min"]} and {limits["max"]}.'
            )

        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE], target_temperature
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE])

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_level = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL])
        if dps_mode is not None:
            if dps_mode is False:
                return HVAC_MODE_OFF
            elif dps_level == POWER_LEVEL_FANONLY:
                return HVAC_MODE_FAN_ONLY
            else:
                return HVAC_MODE_HEAT
        else:
            return STATE_UNAVAILABLE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = True
        if hvac_mode == HVAC_MODE_OFF:
            dps_mode = False

        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode
        )
        dps_level = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL])

        if hvac_mode == HVAC_MODE_FAN_ONLY and dps_level != POWER_LEVEL_FANONLY:
            await self.async_set_preset_mode(PRESET_FAN)
        elif hvac_mode == HVAC_MODE_HEAT and dps_level == POWER_LEVEL_FANONLY:
            await self.async_set_preset_mode(PRESET_AUTO)

    @property
    def preset_mode(self):
        """Return the power level."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL])
        if dps_mode is None:
            return None

        return TuyaLocalDevice.get_key_for_value(POWER_LEVEL_TO_DPS_LEVEL, dps_mode)

    @property
    def preset_modes(self):
        """Retrn the list of available preset modes."""
        return list(POWER_LEVEL_TO_DPS_LEVEL.keys())

    async def async_set_preset_mode(self, preset_mode):
        """Set new power level."""
        dps_mode = POWER_LEVEL_TO_DPS_LEVEL[preset_mode]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL], dps_mode
        )

    @property
    def swing_mode(self):
        """Return the swing mode."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_SWING_MODE])
        if dps_mode is None:
            return None

        if dps_mode:
            return SWING_VERTICAL
        else:
            return SWING_OFF

    @property
    def swing_modes(self):
        """List of swing modes."""
        return [SWING_OFF, SWING_VERTICAL]

    async def async_set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        if swing_mode == SWING_VERTICAL:
            swing_state = True
        elif swing_mode == SWING_OFF:
            swing_state = False
        else:
            raise ValueError(f"Invalid swing mode: {swing_mode}")

        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_SWING_MODE], swing_state
        )

    async def async_update(self):
        await self._device.async_refresh()
