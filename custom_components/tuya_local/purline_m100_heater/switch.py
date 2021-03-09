"""
Platform to control the Open Window Detector on Purline M100 heaters.
"""
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.switch import DEVICE_CLASS_SWITCH

from homeassistant.const import STATE_UNAVAILABLE

from .const import (
    ATTR_OPEN_WINDOW_DETECT,
    PROPERTY_TO_DPS_ID,
)


class PurlineM100OpenWindowDetector(SwitchEntity):
    """Representation of the Open Window Detection of a Purline M100 heater"""

    def __init__(self, device):
        """Initialize the switch.
        Args:
            device (TuyaLocalDevice): The device API instance."""
        self._device = device

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the switch."""
        return self._device.name

    @property
    def unique_id(self):
        """Return the unique id for this switch."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this switch."""
        return self._device.device_info

    @property
    def device_class(self):
        """Return the class of this device"""
        return DEVICE_CLASS_SWITCH

    @property
    def is_on(self):
        """Return the whether the switch is on."""
        is_switched_on = self._device.get_property(
            PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]
        )
        if is_switched_on is None:
            return STATE_UNAVAILABLE
        else:
            return is_switched_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT], True
        )

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT], False
        )

    async def async_update(self):
        await self._device.async_refresh()
