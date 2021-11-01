"""
Platform for Tuya Number options that don't fit into other entity types.
"""
from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import (
    DEFAULT_MIN_VALUE,
    DEFAULT_MAX_VALUE,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig

MODE_AUTO = "auto"


class TuyaLocalNumber(NumberEntity):
    """Representation of a Tuya Number"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        dps_map = {c.name: c for c in config.dps()}
        self._value_dps = dps_map.pop("value")

        if self._value_dps is None:
            raise AttributeError(f"{config.name} is missing a value dps")

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
    def min_value(self):
        r = self._value_dps.range(self._device)
        return DEFAULT_MIN_VALUE if r is None else r["min"]

    @property
    def max_value(self):
        r = self._value_dps.range(self._device)
        return DEFAULT_MAX_VALUE if r is None else r["max"]

    @property
    def step(self):
        return self._value_dps.step(self._device)

    @property
    def mode(self):
        """Return the mode."""
        m = self._config.mode
        if m is None:
            m = MODE_AUTO
        return m

    @property
    def value(self):
        """Return the current value of the number."""
        return self._value_dps.get_value(self._device)

    async def async_set_value(self, value):
        """Set the number."""
        await self._value_dps.async_set_value(self._device, value)

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_update(self):
        await self._device.async_refresh()
