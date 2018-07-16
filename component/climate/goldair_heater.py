"""
Platform to control Goldair WiFi-connected heaters and panels.
"""
from homeassistant.components.climate import (
    ClimateDevice,
    ATTR_OPERATION_MODE, ATTR_TEMPERATURE,
    SUPPORT_ON_OFF, SUPPORT_TARGET_TEMPERATURE, SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE
)
from homeassistant.const import STATE_UNAVAILABLE
import custom_components.goldair_heater as goldair_heater

SUPPORT_FLAGS = SUPPORT_ON_OFF | SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_SWING_MODE


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Goldair WiFi heater."""
    device = hass.data[goldair_heater.DOMAIN][discovery_info['host']]
    add_devices([
        GoldairHeater(device)
    ])


class GoldairHeater(ClimateDevice):
    """Representation of a Goldair WiFi heater."""

    def __init__(self, device):
        """Initialize the heater.
        Args:
            name (str): The device's name.
            device (GoldairHeaterDevice): The device API instance."""
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
    def state(self):
        """Return the state of the climate device."""
        if self._device.is_on is None:
            return STATE_UNAVAILABLE
        else:
            return super().state

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self._device.is_on

    def turn_on(self):
        """Turn on."""
        self._device.turn_on()

    def turn_off(self):
        """Turn off."""
        self._device.turn_off()

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._device.target_temperature_step

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._device.min_target_teperature

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._device.max_target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._device.set_target_temperature(kwargs.get(ATTR_TEMPERATURE))
        if kwargs.get(ATTR_OPERATION_MODE) is not None:
            self._device.set_operation_mode(kwargs.get(ATTR_OPERATION_MODE))

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.current_temperature

    @property
    def current_operation(self):
        """Return current operation, ie Comfort, Eco, Anti-freeze."""
        return self._device.operation_mode

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._device.operation_mode_list

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        self._device.set_operation_mode(operation_mode)

    @property
    def current_swing_mode(self):
        """Return the fan setting."""
        return self._device.power_level

    @property
    def swing_list(self):
        """List of available swing modes."""
        return self._device.power_level_list

    def set_swing_mode(self, swing_mode):
        """Set new target temperature."""
        self._device.set_power_level(swing_mode)

    def update(self):
        self._device.refresh()
