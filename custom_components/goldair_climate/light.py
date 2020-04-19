"""
Setup for different kinds of Goldair climate devices
"""
from homeassistant.const import CONF_HOST
from custom_components.goldair_climate import (
    DOMAIN, CONF_TYPE, CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN, CONF_TYPE_KOGAN_HEATER
)
from custom_components.goldair_climate.heater.light import GoldairHeaterLedDisplayLight
from custom_components.goldair_climate.dehumidifier.light import GoldairDehumidifierLedDisplayLight
from custom_components.goldair_climate.fan.light import GoldairFanLedDisplayLight


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Goldair climate device according to its type."""
    device = hass.data[DOMAIN][discovery_info[CONF_HOST]]
    if discovery_info[CONF_TYPE] == CONF_TYPE_HEATER:
        add_devices([GoldairHeaterLedDisplayLight(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        add_devices([GoldairDehumidifierLedDisplayLight(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        add_devices([GoldairFanLedDisplayLight(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_KOGAN_HEATER:
        raise ValueError('Kogan heaters do not support panel lighting control')
