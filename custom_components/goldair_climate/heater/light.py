"""
Platform to control the LED display light on Goldair WiFi-connected heaters and panels.
"""
from homeassistant.components.light import Light
from homeassistant.const import STATE_UNAVAILABLE
from custom_components.goldair_climate import GoldairTuyaDevice
from custom_components.goldair_climate.heater.climate import (
  ATTR_DISPLAY_ON, GOLDAIR_PROPERTY_TO_DPS_ID, GOLDAIR_MODE_TO_HVAC_MODE
)
from homeassistant.components.climate import (
  ATTR_HVAC_MODE, HVAC_MODE_OFF
)

import logging
_LOGGER = logging.getLogger(__name__)

class GoldairHeaterLedDisplayLight(Light):
    """Representation of a Goldair WiFi-connected heater LED display."""

    def __init__(self, device):
        """Initialize the light.
        Args:
            device (GoldairTuyaDevice): The device API instance."""
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
        dps_hvac_mode = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_display_on = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON])

        if dps_hvac_mode is None or dps_hvac_mode == GOLDAIR_MODE_TO_HVAC_MODE[HVAC_MODE_OFF]:
            return STATE_UNAVAILABLE
        else:
            return dps_display_on

    def turn_on(self):
        self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], True)

    def turn_off(self):
        self._device.set_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], False)

    def toggle(self):
        dps_hvac_mode = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_display_on = self._device.get_property(GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON])

        if dps_hvac_mode != GOLDAIR_MODE_TO_HVAC_MODE[HVAC_MODE_OFF]:
            self.turn_on() if not dps_display_on else self.turn_off()
