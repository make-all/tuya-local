"""
Setup for different kinds of Tuya light devices
"""
from .generic.light import TuyaLocalLight
from .helpers.config import async_tuya_setup_platform


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "light",
        TuyaLocalLight,
    )
