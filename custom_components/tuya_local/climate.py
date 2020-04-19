"""
Setup for different kinds of Tuya climate devices
"""
from homeassistant.const import CONF_HOST
from custom_components.tuya_local import (
    DOMAIN, CONF_TYPE, CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN, CONF_TYPE_KOGAN_HEATER
)
from custom_components.tuya_local.heater.climate import GoldairHeater
from custom_components.tuya_local.dehumidifier.climate import GoldairDehumidifier
from custom_components.tuya_local.fan.climate import GoldairFan
from custom_components.tuya_local.kogan_heater.climate import KoganHeater

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Tuya climate device according to its type."""
    device = hass.data[DOMAIN][discovery_info[CONF_HOST]]
    if discovery_info[CONF_TYPE] == CONF_TYPE_HEATER:
        add_devices([GoldairHeater(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        add_devices([GoldairDehumidifier(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        add_devices([GoldairFan(device)])
    elif discovery_info[CONF_TYPE] == CONF_TYPE_KOGAN_HEATER:
        add_devices([KoganHeater(device)])
