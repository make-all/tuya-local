"""
Setup for different kinds of Tuya selects
"""
from .generic.select import TuyaLocalSelect
from .helpers.config import async_tuya_setup_platform


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the select entity according to it's type."""
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        discovery_info,
        "select",
        TuyaLocalSelect,
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_setup_platform(hass, {}, async_add_entities, config)
