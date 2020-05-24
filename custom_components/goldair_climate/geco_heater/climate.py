"""
Goldair GECO WiFi Heater device.
"""
try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity

from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    HVAC_MODE_HEAT,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from ..device import GoldairTuyaDevice
from .const import (
    ATTR_ERROR,
    ATTR_TARGET_TEMPERATURE,
    HVAC_MODE_TO_DPS_MODE,
    PROPERTY_TO_DPS_ID,
)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE


class GoldairGECOHeater(ClimateEntity):
    """Representation of a Goldair GECO WiFi heater."""

    def __init__(self, device):
        """Initialize the heater.
        Args:
            device (GoldairTuyaDevice): The device API instance."""
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
                f'{limits["min"]} and {limits["max"]}'
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
    def device_state_attributes(self):
        """Get additional attributes that HA doesn't naturally support."""
        error = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ERROR])

        return {ATTR_ERROR: error or None}

    async def async_update(self):
        await self._device.async_refresh()
