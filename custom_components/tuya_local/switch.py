"""
Setup for different kinds of Tuya switch devices
"""
from .generic.switch import TuyaLocalSwitch
from .helpers.config import async_tuya_setup_platform


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch device according to its type."""
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        discovery_info,
        "switch",
        TuyaLocalSwitch,
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_setup_platform(hass, {}, async_add_entities, config)
