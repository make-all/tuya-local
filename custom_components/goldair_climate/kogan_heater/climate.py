"""
Kogan WiFi Heater device.

dps:
  2 = current temperature (integer)
  3 = target temperature (integer)
  4 = preset_mode (string Low/High)
  6 = timer state (boolean) [not supported - use HA based timers]
  7 = hvac_mode (boolean)
  8 = timer (integer) [not supported - use HA based timers]
"""

from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, STATE_UNAVAILABLE
)
from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE, ATTR_PRESET_MODE,
    HVAC_MODE_OFF, HVAC_MODE_HEAT,
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE
)
from custom_components.goldair_climate import GoldairTuyaDevice

ATTR_TARGET_TEMPERATURE = 'target_temperature'

PRESET_LOW = 'LOW'
PRESET_HIGH = 'HIGH'

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: '7',
    ATTR_TARGET_TEMPERATURE: '3',
    ATTR_TEMPERATURE: '2',
    ATTR_PRESET_MODE: '4',
}

HVAC_MODE_TO_DPS_MODE = {
    HVAC_MODE_OFF: False,
    HVAC_MODE_HEAT: True
}

PRESET_MODE_TO_DPS_MODE = {
    PRESET_LOW: 'Low',
    PRESET_HIGH: 'High'
}

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE


class KoganHeater(ClimateDevice):
    """Representation of a Kogan WiFi heater."""

    def __init__(self, device):
        """Initialize the heater.
        Args:
            name (str): The device's name.
            device (GoldairTuyaDevice): The device API instance."""
        self._device = device

        self._support_flags = SUPPORT_FLAGS

        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {
            'min': 16,
            'max': 30
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
        return self._TEMPERATURE_LIMITS['min']

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._TEMPERATURE_LIMITS['max']

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_PRESET_MODE) is not None:
            self.set_preset_mode(kwargs.get(ATTR_PRESET_MODE))
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self.set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    def set_target_temperature(self, target_temperature):
        target_temperature = int(round(target_temperature))

        limits = self._TEMPERATURE_LIMITS
        if not limits['min'] <= target_temperature <= limits['max']:
            raise ValueError(
                f'Target temperature ({target_temperature}) must be between '
                f'{limits["min"]} and {limits["max"]}'
            )

        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE], target_temperature)

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

    def set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = HVAC_MODE_TO_DPS_MODE[hvac_mode]
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode)

    @property
    def preset_mode(self):
        """Return current preset mode, ie Low or High."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE])
        if dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(PRESET_MODE_TO_DPS_MODE, dps_mode)
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

    def update(self):
        self._device.refresh()
