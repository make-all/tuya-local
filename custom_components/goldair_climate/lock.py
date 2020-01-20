"""
Setup for different kinds of Goldair climate devices
"""
from homeassistant.const import CONF_HOST
from custom_components.goldair_climate import (
    DOMAIN, CONF_TYPE, CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN
)
from custom_components.goldair_climate.heater.lock import GoldairHeaterChildLock
from custom_components.goldair_climate.dehumidifier.lock import GoldairDehumidifierChildLock


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Goldair climate device according to its type."""
    device = hass.data[DOMAIN][discovery_info[CONF_HOST]]
    if discovery_info[CONF_TYPE] == CONF_TYPE_HEATER:
        add_devices([GoldairHeaterChildLock(device)])
    if discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        add_devices([GoldairDehumidifierChildLock(device)])
    if discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        raise ValueError('Goldair fains do not support Child Lock.')
