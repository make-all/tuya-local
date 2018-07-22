"""
Platform to control the LED display light on Goldair WiFi-connected heaters and panels.
"""
from homeassistant.components.light import Light
from homeassistant.const import STATE_UNAVAILABLE
import custom_components.goldair_heater as goldair_heater


def setup_platform(hass, config, add_devices, discovery_info=None):
    device = hass.data[goldair_heater.DOMAIN][discovery_info['host']]
    add_devices([
        GoldairLedDisplayLight(device)
    ])


class GoldairLedDisplayLight(Light):
    """Representation of a Goldair WiFi-connected heater LED display."""

    def __init__(self, device):
        """Initialize the light.
        Args:
            device (GoldairHeaterDevice): The device API instance."""
        self._device = device

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the light."""
        return self._device.name

    @property
    def is_on(self):
        """Return the current state."""
        if self._device.is_on is None:
            return STATE_UNAVAILABLE
        else:
            return self._device.is_on and self._device.is_display_on

    def turn_on(self):
        """Turn on the LED display."""
        self._device.turn_display_on()

    def turn_off(self):
        """Turn off the LED display."""
        self._device.turn_display_off()

    def toggle(self):
        self._device.turn_display_on() if not self._device.is_display_on else self._device.turn_display_off()
