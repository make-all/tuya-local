"""
Platform to control the switch on Kogan WiFi-connected energy monitoring sockets.
"""
from homeassistant.components.switch import SwitchEntity
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
    ATTR_ALT_TIMER,
    ATTR_ALT_CURRENT_A,
    ATTR_ALT_CURRENT_POWER_W,
    ATTR_ALT_VOLTAGE_V,
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
        is_switched_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_SWITCH])
        if is_switched_on is None:
            return STATE_UNAVAILABLE
        else:
            return is_switched_on

    @property
    def current_power_w(self):
        """Return the current power consumption in Watts"""
        pwr = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_CURRENT_POWER_W])
        if pwr is None:
            # Some newer plugs have the measurements on different DPS ids
            pwr = self._device.get_property(
                PROPERTY_TO_DPS_ID[ATTR_ALT_CURRENT_POWER_W]
            )
            if pwr is None:
                return STATE_UNAVAILABLE

        return pwr / 10.0

    @property
    def device_state_attributes(self):
        """Get additional attributes that HA doesn't naturally support."""
        timer = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TIMER])
        voltage = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_VOLTAGE_V])
        current = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_CURRENT_A])

        # Some newer plugs have the measurements on different DPS ids
        if timer is None:
            timer = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ALT_TIMER])

        if voltage is None:
            voltage = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ALT_VOLTAGE_V])

        if current is None:
            current = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ALT_CURRENT_A])

        return {
            ATTR_CURRENT_POWER_W: self.current_power_w,
            ATTR_CURRENT_A: None if current is None else current / 1000.0,
            ATTR_VOLTAGE_V: None if voltage is None else voltage / 10.0,
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
