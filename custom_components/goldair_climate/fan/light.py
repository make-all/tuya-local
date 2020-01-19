"""
Platform to control the LED display light on Goldair WiFi-connected fans and panels.
"""
from homeassistant.components.light import Light
from homeassistant.const import STATE_UNAVAILABLE
from custom_components.goldair_climate import GoldairTuyaDevice
from custom_components.goldair_climate.fan.climate import (
    ATTR_DISPLAY_ON, PROPERTY_TO_DPS_ID, HVAC_MODE_TO_DPS_MODE
)
from homeassistant.components.climate import (
    ATTR_HVAC_MODE, HVAC_MODE_OFF
)


class GoldairFanLedDisplayLight(Light):
    """Representation of a Goldair WiFi-connected fan LED display."""

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
        dps_hvac_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_display_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON])

        if dps_hvac_mode is None or dps_hvac_mode == HVAC_MODE_TO_DPS_MODE[HVAC_MODE_OFF]:
            return STATE_UNAVAILABLE
        else:
            return dps_display_on

    def turn_on(self):
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], True)

    def turn_off(self):
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], False)

    def toggle(self):
        dps_hvac_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_display_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON])

        if dps_hvac_mode != HVAC_MODE_TO_DPS_MODE[HVAC_MODE_OFF]:
            self.turn_on() if not dps_display_on else self.turn_off()
