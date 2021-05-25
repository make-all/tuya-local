"""
Platform to control Tuya switches.
Initially based on the Kogan Switch and secondary switch for Purline M100
heater open window detector toggle.
"""
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.switch import (
    ATTR_CURRENT_POWER_W,
    DEVICE_CLASS_OUTLET,
    DEVICE_CLASS_SWITCH,
)

from homeassistant.const import STATE_UNAVAILABLE

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig


class TuyaLocalSwitch(SwitchEntity):
    """Representation of a Tuya Switch"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the switch.
        Args:
            device (TuyaLocalDevice): The device API instance.
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        for d in config.dps():
            if d.name == "switch":
                self._switch_dps = d
            else:
                if d.name == "current_power_w":
                    self._power_dps = d
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self._device.name

    @property
    def friendly_name(self):
        """Return the friendly name for this entity."""
        return self._config.name

    @property
    def unique_id(self):
        """Return the unique id of the device."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about the device."""
        return self._device.device_info

    @property
    def device_class(self):
        """Return the class of this device"""
        return (
            DEVICE_CLASS_OUTLET
            if self._config.device_class == "outlet"
            else DEVICE_CLASS_SWITCH
        )

    @property
    def is_on(self):
        """Return whether the switch is on or not."""
        is_switched_on = self._switch_dps.map_from_dps(
            self._device.get_property(self._switch_dps.id)
        )

        if is_switched_on is None:
            return STATE_UNAVAILABLE
        else:
            return is_switched_on

    @property
    def current_power_w(self):
        """Return the current power consumption in Watts."""
        if self._power_dps is None:
            return None

        pwr = self._power_dps.map_from_dps(
            self._device.get_property(self._power_dps.id)
        )
        if pwr is None:
            return STATE_UNAVAILABLE

        return pwr

    @property
    def device_state_attributes(self):
        """Get additional attributes that HA doesn't naturally support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.map_from_dps(self._device.get_property(a.id))
        return attr

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._device.async_set_property(
            self._switch_dps.id, self._switch_dps.map_to_dps(True)
        )

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._device.async_set_property(
            self._switch_dps.id, self._switch_dps.map_to_dps(False)
        )

    async def async_update(self):
        await self._device.async_refresh()
