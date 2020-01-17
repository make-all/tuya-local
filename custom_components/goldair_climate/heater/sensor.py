"""
Platform to sense the current temperature at a Goldair WiFi-connected heaters and panels.
"""
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    STATE_UNAVAILABLE, ATTR_TEMPERATURE
)
from custom_components.goldair_climate import GoldairTuyaDevice
from custom_components.goldair_climate.heater.climate import GOLDAIR_PROPERTY_TO_DPS_ID

class GoldairHeaterTemperatureSensor(Entity):
    """Representation of a Goldair WiFi-connected heater thermometer."""

    def __init__(self, device):
        """Initialize the lock.
        Args:
            device (GoldairTuyaDevice): The device API instance."""
        self._device = device

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device.name

    @property
    def state(self):
        """Return the current temperature."""
        current_temperature = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE])
        if current_temperature is None:
            return STATE_UNAVAILABLE
        else:
            return current_temperature

    @property
    def unit_of_measurement(self):
        return self._device.temperature_unit
