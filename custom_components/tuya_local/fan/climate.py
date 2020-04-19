"""
Goldair WiFi Fan device.
"""
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, STATE_UNAVAILABLE
)
from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE, ATTR_PRESET_MODE, ATTR_FAN_MODE, ATTR_SWING_MODE,
    HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY,
    PRESET_ECO, PRESET_SLEEP,
    SUPPORT_FAN_MODE, SUPPORT_PRESET_MODE, SUPPORT_SWING_MODE,
    SWING_OFF, SWING_HORIZONTAL
)
from custom_components.tuya_local import TuyaLocalDevice

ATTR_TARGET_TEMPERATURE = 'target_temperature'
ATTR_DISPLAY_ON = 'display_on'

PRESET_NORMAL = 'normal'

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: '1',
    ATTR_FAN_MODE: '2',
    ATTR_PRESET_MODE: '3',
    ATTR_SWING_MODE: '8',
    ATTR_DISPLAY_ON: '101'
}

HVAC_MODE_TO_DPS_MODE = {
    HVAC_MODE_OFF: False,
    HVAC_MODE_FAN_ONLY: True
}
PRESET_MODE_TO_DPS_MODE = {
    PRESET_NORMAL: 'normal',
    PRESET_ECO: 'nature',
    PRESET_SLEEP: 'sleep'
}
SWING_MODE_TO_DPS_MODE = {
    SWING_OFF: False,
    SWING_HORIZONTAL: True
}
FAN_MODES = {
    PRESET_NORMAL: {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10', 11: '11',
                    12: '12'},
    PRESET_ECO: {1: '4', 2: '8', 3: '12'},
    PRESET_SLEEP: {1: '4', 2: '8', 3: '12'}
}

SUPPORT_FLAGS = SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE


class GoldairFan(ClimateDevice):
    """Representation of a Goldair WiFi fan."""

    def __init__(self, device):
        """Initialize the fan.
        Args:
            name (str): The device's name.
            device (TuyaLocalDevice): The device API instance."""
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
    def temperature_unit(self):
        """This is not used but required by Home Assistant."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Fan Only or Off."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])

        if dps_mode is not None:
            return TuyaLocalDevice.get_key_for_value(HVAC_MODE_TO_DPS_MODE, dps_mode)
        else:
            return STATE_UNAVAILABLE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return list(HVAC_MODE_TO_DPS_MODE.keys())

    def set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = HVAC_MODE_TO_DPS_MODE[hvac_mode]
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode)

    @property
    def preset_mode(self):
        """Return current preset mode, ie Comfort, Eco, Anti-freeze."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE])
        if dps_mode is not None:
            return TuyaLocalDevice.get_key_for_value(PRESET_MODE_TO_DPS_MODE, dps_mode)
        else:
            return None

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return list(PRESET_MODE_TO_DPS_MODE.keys())

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        dps_mode = PRESET_MODE_TO_DPS_MODE[preset_mode]
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE], dps_mode)

    @property
    def swing_mode(self):
        """Return current swing mode: horizontal or off"""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_SWING_MODE])
        if dps_mode is not None:
            return TuyaLocalDevice.get_key_for_value(SWING_MODE_TO_DPS_MODE, dps_mode)
        else:
            return None

    @property
    def swing_modes(self):
        """Return the list of available swing modes."""
        return list(SWING_MODE_TO_DPS_MODE.keys())

    def set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        dps_mode = SWING_MODE_TO_DPS_MODE[swing_mode]
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_SWING_MODE], dps_mode)

    @property
    def fan_mode(self):
        """Return current fan mode: 1-12"""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE])
        if dps_mode is not None and self.preset_mode is not None:
            return TuyaLocalDevice.get_key_for_value(FAN_MODES[self.preset_mode], dps_mode)
        else:
            return None

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        if self.preset_mode is not None:
            return list(FAN_MODES[self.preset_mode].keys())
        else:
            return []

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        if self.preset_mode is not None:
            dps_mode = FAN_MODES[self.preset_mode][int(fan_mode)]
            self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], dps_mode)

    def update(self):
        self._device.refresh()
