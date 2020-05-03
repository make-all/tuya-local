"""
Platform to control the LED display light on Goldair WiFi-connected heaters and panels.
"""
from homeassistant.components.climate import ATTR_HVAC_MODE, HVAC_MODE_OFF
from homeassistant.components.light import Light
from homeassistant.const import STATE_UNAVAILABLE

from ..device import GoldairTuyaDevice
from .const import ATTR_DISPLAY_ON, HVAC_MODE_TO_DPS_MODE, PROPERTY_TO_DPS_ID


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
    def unique_id(self):
        """Return the unique id for this heater LED display."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this heater LED display."""
        return self._device.device_info

    @property
    def is_on(self):
        """Return the current state."""
        dps_hvac_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_display_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON])

        if (
            dps_hvac_mode is None
            or dps_hvac_mode == HVAC_MODE_TO_DPS_MODE[HVAC_MODE_OFF]
        ):
            return STATE_UNAVAILABLE
        else:
            return dps_display_on

    async def async_turn_on(self):
        await self._device.async_set_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], True)

    async def async_turn_off(self):
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], False
        )

    async def async_toggle(self):
        dps_hvac_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])
        dps_display_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON])

        if dps_hvac_mode != HVAC_MODE_TO_DPS_MODE[HVAC_MODE_OFF]:
            await (
                self.async_turn_on() if not dps_display_on else self.async_turn_off()
            )

    async def async_update(self):
        await self._device.async_refresh()
