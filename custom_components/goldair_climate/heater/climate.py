"""
Goldair WiFi Heater device.
"""
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, STATE_UNAVAILABLE
)
from homeassistant.components.climate import (
  ClimateDevice, ATTR_HVAC_MODE, ATTR_PRESET_MODE, ATTR_TEMPERATURE, HVAC_MODE_OFF, HVAC_MODE_HEAT
)
from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE, SUPPORT_SWING_MODE
)
from custom_components.goldair_climate import GoldairTuyaDevice

ATTR_ON = 'on'
ATTR_TARGET_TEMPERATURE = 'target_temperature'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_FAULT = 'fault'
ATTR_POWER_MODE_AUTO = 'auto'
ATTR_POWER_MODE_USER = 'user'
ATTR_POWER_LEVEL = 'power_level'
ATTR_TIMER_MINUTES = 'timer_minutes'
ATTR_TIMER_ON = 'timer_on'
ATTR_DISPLAY_ON = 'display_on'
ATTR_POWER_MODE = 'power_mode'
ATTR_ECO_TARGET_TEMPERATURE = 'eco_' + ATTR_TARGET_TEMPERATURE

STATE_COMFORT = 'Comfort'
STATE_ECO = 'Eco'
STATE_ANTI_FREEZE = 'Anti-freeze'

GOLDAIR_PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: '1',
    ATTR_TARGET_TEMPERATURE: '2',
    ATTR_TEMPERATURE: '3',
    ATTR_PRESET_MODE: '4',
    ATTR_CHILD_LOCK: '6',
    ATTR_FAULT: '12',
    ATTR_POWER_LEVEL: '101',
    ATTR_TIMER_MINUTES: '102',
    ATTR_TIMER_ON: '103',
    ATTR_DISPLAY_ON: '104',
    ATTR_POWER_MODE: '105',
    ATTR_ECO_TARGET_TEMPERATURE: '106'
}

GOLDAIR_MODE_TO_HVAC_MODE = {
    HVAC_MODE_OFF: False,
    HVAC_MODE_HEAT: True
}
GOLDAIR_MODE_TO_PRESET_MODE = {
    STATE_COMFORT: 'C',
    STATE_ECO: 'ECO',
    STATE_ANTI_FREEZE: 'AF'
}
GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL = {
    'Stop': 'stop',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    'Auto': 'auto'
}
GOLDAIR_POWER_MODES = [ATTR_POWER_MODE_USER, ATTR_POWER_MODE_USER]

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE

class GoldairHeater(ClimateDevice):
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
            STATE_COMFORT: {
                'min': 5,
                'max': 35
            },
            STATE_ECO: {
                'min': 5,
                'max': 21
            }
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
    def state(self):
        """Return the state of the climate device."""
        return self.hvac_mode

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.preset_mode == STATE_COMFORT:
            return self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE])
        elif self.preset_mode == STATE_ECO:
            return self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_ECO_TARGET_TEMPERATURE])
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
            return self._TEMPERATURE_LIMITS[self.preset_mode]['min']
        else:
            return None

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self.preset_mode and self.preset_mode != STATE_ANTI_FREEZE:
            return self._TEMPERATURE_LIMITS[self.preset_mode]['max']
        else:
            return None

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_PRESET_MODE) is not None:
            self.set_preset_mode(kwargs.get(ATTR_PRESET_MODE))
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self.set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    def set_target_temperature(self, target_temperature):
        target_temperature = int(round(target_temperature))
        preset_mode = self.preset_mode

        if preset_mode == STATE_ANTI_FREEZE:
            raise ValueError('You cannot set the temperature in Anti-freeze mode.')

        limits = self._TEMPERATURE_LIMITS[preset_mode]
        if not limits['min'] <= target_temperature <= limits['max']:
            raise ValueError(
                f'Target temperature ({target_temperature}) must be between '
                f'{limits["min"]} and {limits["max"]}'
            )

        if preset_mode == STATE_COMFORT:
            self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE], target_temperature)
        elif preset_mode == STATE_ECO:
            self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_ECO_TARGET_TEMPERATURE], target_temperature)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE])

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        dps_mode = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])

        if dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(GOLDAIR_MODE_TO_HVAC_MODE, dps_mode)
        else:
            return STATE_UNAVAILABLE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return list(GOLDAIR_MODE_TO_HVAC_MODE.keys())

    def set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = GOLDAIR_MODE_TO_HVAC_MODE[hvac_mode]
        self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode)

    @property
    def preset_mode(self):
        """Return current preset mode, ie Comfort, Eco, Anti-freeze."""
        dps_mode = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE])
        if dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(GOLDAIR_MODE_TO_PRESET_MODE, dps_mode)
        else:
            return None

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return list(GOLDAIR_MODE_TO_PRESET_MODE.keys())

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        dps_mode = GOLDAIR_MODE_TO_PRESET_MODE[preset_mode]
        self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE], dps_mode)

    @property
    def swing_mode(self):
        """Return the power level."""
        dps_mode = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_POWER_MODE])
        if dps_mode == ATTR_POWER_MODE_USER:
            return self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL])
        elif dps_mode == ATTR_POWER_MODE_AUTO:
            return GoldairTuyaDevice.get_key_for_value(GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL, dps_mode)
        else:
            return None

    @property
    def swing_modes(self):
        """List of power levels."""
        return list(GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL.keys())

    def set_swing_mode(self, swing_mode):
        """Set new power level."""
        new_level = swing_mode
        if new_level not in GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL.keys():
            raise ValueError(f'Invalid power level: {new_level}')
        dps_level = GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL[new_level]
        self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL], dps_level)

    def update(self):
        self._device.refresh()
