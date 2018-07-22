"""
Platform to sense the current temperature at a Goldair WiFi-connected heaters and panels.
"""
from homeassistant.helpers.entity import Entity
from homeassistant.const import STATE_UNAVAILABLE
import custom_components.goldair_heater as goldair_heater


def setup_platform(hass, config, add_devices, discovery_info=None):
    device = hass.data[goldair_heater.DOMAIN][discovery_info['host']]
    add_devices([
        GoldairTemperatureSensor(device)
    ])


class GoldairTemperatureSensor(Entity):
    """Representation of a Goldair WiFi-connected heater thermometer."""

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
    def state(self):
        """Return the current state."""
        if self._device.current_temperature is None:
            return STATE_UNAVAILABLE
        else:
            return self._device.current_temperature

    @property
    def unit_of_measurement(self):
        return self._device.temperature_unit
