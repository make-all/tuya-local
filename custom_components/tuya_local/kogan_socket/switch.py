"""
Platform to control the switch on Kogan WiFi-connected energy monitoring sockets.
"""
try:
    from homeassistant.components.switch import SwitchEntity
except ImportError:
    from homeassistant.components.switch import SwitchDevice as SwitchEntity

from homeassistant.components.switch import (
    ATTR_CURRENT_POWER_W,
    DEVICE_CLASS_OUTLET,
)

from homeassistant.const import STATE_UNAVAILABLE

from .const import (
    ATTR_CURRENT_A,
    ATTR_SWITCH,
    ATTR_TIMER,
    ATTR_VOLTAGE_V,
    PROPERTY_TO_DPS_ID,
)


class KoganSocketSwitch(SwitchEntity):
    """Representation of a Kogan WiFi-connected energy monitoring socket"""

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
        return DEVICE_CLASS_OUTLET

    @property
    def is_on(self):
        """Return the whether the switch is on."""
        if self.is_switched_on is None:
            return STATE_UNAVAILABLE
        else:
            return self.is_switched_on

    @property
    def current_power_w(self):
        """Return the current power consumption in Watts"""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_CURRENT_POWER_W]) / 10.0

    @property
    def device_state_attributes(self):
        """Get additional attributes that HA doesn't naturally support."""
        timer = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TIMER])
        voltage = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_VOLTAGE_V]) / 10.0
        current = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_CURRENT_A]) / 1000.0
        return {
            ATTR_CURRENT_POWER_W: self.current_power_w,
            ATTR_CURRENT_A: current,
            ATTR_VOLTAGE_V: voltage,
            ATTR_TIMER: timer,
        }

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._device.async_set_property(PROPERTY_TO_DPS_ID[ATTR_SWITCH], True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._device.async_set_property(PROPERTY_TO_DPS_ID[ATTR_SWITCH], False)

    async def async_update(self):
        await self._device.async_refresh()
