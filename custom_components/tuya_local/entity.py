"""
Common functionality for Tuya Local entities
"""

import json
import logging
from numbers import Number

from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    UnitOfArea,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

# These attributes should not be included in the extra state attributes
BLACKLISTED_ATTRIBUTES = ["state", "available"]


class TuyaLocalEntity:
    """Common functions for all entity types."""

    def _init_begin(self, device, config):
        self._device = device
        self._config = config
        self._attr_dps = []
        self._cal_prefix = slugify(config.config_id)
        self._attr_translation_key = (
            config.translation_key or config.translation_only_key
        )
        self._attr_translation_placeholders = config.translation_placeholders

        return {c.name: c for c in config.dps()}

    def _init_end(self, dps):
        for d in dps.values():
            if not d.hidden and d.name not in BLACKLISTED_ATTRIBUTES:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._device.has_returned_state and self._config.available(self._device)

    @property
    def has_entity_name(self):
        return True

    @property
    def name(self):
        """Return the name for the UI."""
        own_name = self._config.name
        if not own_name and not self.use_device_name:
            # super has the translation logic
            own_name = super().name
        return own_name

    @property
    def use_device_name(self):
        """Return whether to use the device name for the entity name"""
        own_name = (
            self._config.name
            or self._config.translation_key
            or (self._default_to_device_class_name() and self._config.device_class)
        )
        return not own_name

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
        return (
            None
            if self._config.entity_category is None
            else EntityCategory(self._config.entity_category)
        )

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
            value = a.get_value(self._device)
            if value is not None or not a.optional:
                # Decode json attributes for user convenience
                if a.rawtype == "json":
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        if value is not None:
                            _LOGGER.warning(
                                "Failed to decode JSON for attribute %s: %s",
                                a.name,
                                value,
                            )
                attr[a.name] = value
        # Surface user-set calibration offsets for transparency. The loop
        # covers all dps of the entity (not just leftover attribute dps)
        # because the calibrated reading is usually a popped platform dp.
        get_cal = getattr(self._device, "get_calibration", None)
        if get_cal and getattr(self._device, "has_calibration", False):
            for dp in self._config.dps():
                offset = get_cal(self._cal_prefix, dp.name)
                if isinstance(offset, Number):
                    key = f"{dp.name}_calibration"
                    # never shadow a real dp attribute of the same name
                    if key not in attr:
                        attr[key] = offset
        return attr

    @property
    def entity_registry_enabled_default(self):
        """Disable deprecated entities on new installations"""
        return self._config.enabled_by_default(self._device)

    async def async_update(self):
        await self._device.async_refresh()

    async def async_added_to_hass(self):
        self._device.register_entity(self)
        _LOGGER.debug("Adding %s for %s", self._config.config_id, self._device.name)
        if self._config.deprecated:
            _LOGGER.warning(self._config.deprecation_message)

    async def async_will_remove_from_hass(self):
        _LOGGER.debug("Removing %s for %s", self._config.config_id, self._device.name)
        await self._device.async_unregister_entity(self)

    def on_receive(self, dps, full_poll):
        """Override to process dps directly as they are received"""
        pass


UNIT_ASCII_MAP = {
    "C": UnitOfTemperature.CELSIUS.value,
    "F": UnitOfTemperature.FAHRENHEIT.value,
    "ugm3": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    "m2": UnitOfArea.SQUARE_METERS,
}


def unit_from_ascii(unit):
    if unit in UNIT_ASCII_MAP:
        return UNIT_ASCII_MAP[unit]

    return unit
