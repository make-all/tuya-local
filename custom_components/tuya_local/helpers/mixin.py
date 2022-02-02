"""
Mixins to make writing new platforms easier
"""
import logging
from homeassistant.const import (
    AREA_SQUARE_METERS,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

_LOGGER = logging.getLogger(__name__)


class TuyaLocalEntity:
    """Common functions for all entity types."""

    def _init_begin(self, device, config):
        self._device = device
        self._config = config
        self._attr_dps = []
        return {c.name: c for c in config.dps()}

    def _init_end(self, dps):
        for d in dps.values():
            if not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        return True

    @property
    def available(self):
        return self._device.has_returned_state

    @property
    def name(self):
        """Return the name for the UI."""
        return self._config.name(self._device.name)

    @property
    def unique_id(self):
        """Return the unique id for this entity."""
        return self._config.unique_id(self._device.unique_id)

    @property
    def device_info(self):
        """Return the device's information."""
        return self._device.device_info

    @property
    def entity_category(self):
        """Return the entitiy's category."""
        return self._config.entity_category

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        icon = self._config.icon(self._device)
        if icon:
            return icon
        else:
            return super().icon

    @property
    def extra_state_attributes(self):
        """Get additional attributes that the platform itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_update(self):
        await self._device.async_refresh()


UNIT_ASCII_MAP = {
    "C": TEMP_CELSIUS,
    "F": TEMP_FAHRENHEIT,
    "ugm3": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    "m2": AREA_SQUARE_METERS,
}


def unit_from_ascii(unit):
    if unit in UNIT_ASCII_MAP:
        return UNIT_ASCII_MAP[unit]

    return unit
