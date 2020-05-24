"""
Goldair WiFi Fan device.
"""
try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity

from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE, TEMP_CELSIUS

from ..device import GoldairTuyaDevice
from .const import (
    FAN_MODES,
    HVAC_MODE_TO_DPS_MODE,
    PRESET_MODE_TO_DPS_MODE,
    PROPERTY_TO_DPS_ID,
    SWING_MODE_TO_DPS_MODE,
)

SUPPORT_FLAGS = SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE


class GoldairFan(ClimateEntity):
    """Representation of a Goldair WiFi fan."""

    def __init__(self, device):
        """Initialize the fan.
        Args:
            name (str): The device's name.
            device (GoldairTuyaDevice): The device API instance."""
        self._device = device

        self._support_flags = SUPPORT_FLAGS

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
        """Return the unique id for this fan."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this fan."""
        return self._device.device_info

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fan"

    @property
    def temperature_unit(self):
        """This is not used but required by Home Assistant."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Fan Only or Off."""
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
        """Return current swing mode: horizontal or off"""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_SWING_MODE])
        if dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(SWING_MODE_TO_DPS_MODE, dps_mode)
        else:
            return None

    @property
    def swing_modes(self):
        """Return the list of available swing modes."""
        return list(SWING_MODE_TO_DPS_MODE.keys())

    async def async_set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        dps_mode = SWING_MODE_TO_DPS_MODE[swing_mode]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_SWING_MODE], dps_mode
        )

    @property
    def fan_mode(self):
        """Return current fan mode: 1-12"""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE])
        if (
            dps_mode is not None
            and self.preset_mode is not None
            and dps_mode in FAN_MODES[self.preset_mode].values()
        ):
            return GoldairTuyaDevice.get_key_for_value(
                FAN_MODES[self.preset_mode], dps_mode
            )
        else:
            return None

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        if self.preset_mode is not None:
            return list(FAN_MODES[self.preset_mode].keys())
        else:
            return []

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        if self.preset_mode is not None:
            dps_mode = FAN_MODES[self.preset_mode][int(fan_mode)]
            await self._device.async_set_property(
                PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], dps_mode
            )

    async def async_update(self):
        await self._device.async_refresh()
