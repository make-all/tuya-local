"""
Platform for Tuya Select options that don't fit into other entity types.
"""
from homeassistant.components.select import SelectEntity

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig


class TuyaLocalSelect(SelectEntity):
    """Representation of a Tuya Select"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the select.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        dps_map = {c.name: c for c in config.dps()}
        self._option_dps = dps_map.pop("option")

        if self._option_dps is None:
            raise AttributeError(f"{config.name} is missing an option dps")
        if not self._option_dps.values(device):
            raise AttributeError(
                f"{config.name} does not have a mapping to a list of options"
            )

        for d in dps_map.values():
            if not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def available(self):
        """Return whether the switch is available."""
        return self._device.has_returned_state

    @property
    def name(self):
        """Return the name for this entity."""
        return self._config.name(self._device.name)

    @property
    def unique_id(self):
        """Return the unique id of the device."""
        return self._config.unique_id(self._device.unique_id)

    @property
    def device_info(self):
        """Return device information about this device."""
        return self._device.device_info

    @property
    def options(self):
        "Return the list of possible options."
        return self._option_dps.values(self._device)

    @property
    def current_option(self):
        "Return the currently selected option"
        return self._option_dps.get_value(self._device)

    async def async_select_option(self, option):
        "Set the option"
        await self._option_dps.async_set_value(self._device, option)

    @property
    def device_state_attributes(self):
        """Get additional attributes."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_update(self):
        """Update the device state."""
        await self._device.async_refresh()
