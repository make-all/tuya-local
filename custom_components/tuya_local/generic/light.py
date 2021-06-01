"""
Platform to control Tuya lights.
Initially based on the secondary panel lighting control on some climate
devices, so only providing simple on/off control.
"""
from homeassistant.components.light import LightEntity

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig


class TuyaLocalLight(LightEntity):
    """Representation of a Tuya WiFi-connected light."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the light.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The configuration for this entity.
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        for d in config.dps():
            if d.name == "switch":
                self._switch_dps = d
            elif not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the light."""
        return self._device.name

    @property
    def friendly_name(self):
        """Return the friendly name for this entity."""
        return self._config.name

    @property
    def unique_id(self):
        """Return the unique id for this heater LED display."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this heater LED display."""
        return self._device.device_info

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:led-on"
        else:
            return "mdi:led-off"

    @property
    def is_on(self):
        """Return the current state."""
        return self._switch_dps.get_value(self._device)

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_turn_on(self):
        await self._switch_dps.async_set_value(self._device, True)

    async def async_turn_off(self):
        await self._switch_dps.async_set_value(self._device, False)

    async def async_toggle(self):
        dps_display_on = self.is_on

        await (self.async_turn_on() if not dps_display_on else self.async_turn_off())

    async def async_update(self):
        await self._device.async_refresh()
