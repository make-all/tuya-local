"""
Setup for different kinds of Goldair climate devices
"""
from . import DOMAIN
from .const import (CONF_DEVICE_ID, CONF_TYPE, CONF_TYPE_DEHUMIDIFIER,
                    CONF_TYPE_FAN, CONF_TYPE_HEATER)
from .dehumidifier.climate import GoldairDehumidifier
from .fan.climate import GoldairFan
from .heater.climate import GoldairHeater


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Goldair climate device according to its type."""
    device = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    if discovery_info[CONF_TYPE] == CONF_TYPE_HEATER:
        async_add_entities([GoldairHeater(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        async_add_entities([GoldairDehumidifier(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        async_add_entities([GoldairFan(device)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
