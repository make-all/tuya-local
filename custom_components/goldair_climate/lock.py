"""
Setup for different kinds of Goldair climate devices
"""
from . import DOMAIN
from .const import (CONF_DEVICE_ID, CONF_TYPE, CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN)
from .heater.lock import GoldairHeaterChildLock
from .dehumidifier.lock import GoldairDehumidifierChildLock


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Goldair climate device according to its type."""
    device = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    if discovery_info[CONF_TYPE] == CONF_TYPE_HEATER:
        async_add_devices([GoldairHeaterChildLock(device)])
    if discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        async_add_devices([GoldairDehumidifierChildLock(device)])
    if discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        raise ValueError('Goldair fains do not support Child Lock.')


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE]
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
