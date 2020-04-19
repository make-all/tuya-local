"""
Setup for different kinds of Tuya climate devices
"""
from homeassistant.const import CONF_HOST
from custom_components.tuya_local import (
    DOMAIN, CONF_TYPE, CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN, CONF_TYPE_KOGAN_HEATER
)
from custom_components.tuya_local.heater.light import GoldairHeaterLedDisplayLight
from custom_components.tuya_local.dehumidifier.light import GoldairDehumidifierLedDisplayLight
from custom_components.tuya_local.fan.light import GoldairFanLedDisplayLight


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Tuya climate device according to its type."""
    device = hass.data[DOMAIN][discovery_info[CONF_HOST]]
    if discovery_info[CONF_TYPE] == CONF_TYPE_HEATER:
        add_devices([GoldairHeaterLedDisplayLight(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        add_devices([GoldairDehumidifierLedDisplayLight(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        add_devices([GoldairFanLedDisplayLight(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_KOGAN_HEATER:
        raise ValueError('Kogan heaters do not support panel lighting control')
