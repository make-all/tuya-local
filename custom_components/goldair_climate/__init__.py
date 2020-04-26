"""
Platform for Goldair WiFi-connected heaters and panels.

Based on sean6541/tuya-homeassistant for service call logic, and TarxBoy's
investigation into Goldair's tuyapi statuses
https://github.com/codetheweb/tuyapi/issues/31.
"""
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_NAME, CONF_HOST)
from homeassistant.helpers.discovery import async_load_platform

from .const import (
    CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_TYPE, CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN,
    CONF_CLIMATE, CONF_DISPLAY_LIGHT, CONF_CHILD_LOCK
)
from .device import GoldairTuyaDevice

import logging

_LOGGER = logging.getLogger(__name__)

VERSION = '0.0.8'

DOMAIN = 'goldair_climate'
DATA_GOLDAIR_CLIMATE = 'data_goldair_climate'

INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE = [
    {'key': CONF_NAME, 'type': str, 'required': True},
    {'key': CONF_HOST, 'type': str, 'required': True},
    {'key': CONF_DEVICE_ID, 'type': str, 'required': True, 'fixed': True},
    {'key': CONF_LOCAL_KEY, 'type': str, 'required': True},
    {
        'key': CONF_TYPE,
        'type': vol.In([CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN]),
        'required': True,
        'fixed': True
    },
    {'key': CONF_CLIMATE, 'type': bool, 'required': False, 'default': True},
    {'key': CONF_DISPLAY_LIGHT, 'type': bool, 'required': False, 'default': False},
    {'key': CONF_CHILD_LOCK, 'type': bool, 'required': False, 'default': False}
]


def individual_config_schema(defaults={}, exclude_fixed=False):
    output = {}

    for prop in INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE:
        if exclude_fixed and prop.get('fixed'):
            continue

        options = {}

        default = defaults.get(prop['key'], prop.get('default'))
        if default is not None:
            options['default'] = default

        key = vol.Required(prop['key'], **options) if prop['required'] else vol.Optional(prop['key'], **options)
        output[key] = prop['type']

    return output


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(cv.ensure_list, [vol.Schema(individual_config_schema())])
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    hass.data[DOMAIN] = {}

    for device_config in config.get(DOMAIN, []):
        setup_device(hass, device_config)

        discovery_info = {
            CONF_DEVICE_ID: device_config.get(CONF_DEVICE_ID),
            CONF_TYPE: device_config.get(CONF_TYPE)
        }

        if device_config.get(CONF_CLIMATE) == True:
            hass.async_create_task(
                async_load_platform(hass, 'climate', DOMAIN, discovery_info, config)
            )
        if device_config.get(CONF_DISPLAY_LIGHT) == True:
            hass.async_create_task(
                async_load_platform(hass, 'light', DOMAIN, discovery_info, config)
            )
        if device_config.get(CONF_CHILD_LOCK) == True:
            hass.async_create_task(
                async_load_platform(hass, 'lock', DOMAIN, discovery_info, config)
            )

    return True


async def async_setup_entry(hass, entry):
    config = {**entry.data, **entry.options}
    setup_device(hass, config)

    if config[CONF_CLIMATE] == True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, 'climate')
        )
    if config[CONF_DISPLAY_LIGHT] == True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, 'light')
        )
    if config[CONF_CHILD_LOCK] == True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, 'lock')
        )

    entry.add_update_listener(async_update_entry)

    return True


async def async_unload_entry(hass, entry):
    config = entry.data
    delete_device(hass, config)

    if config[CONF_CLIMATE] == True:
        await hass.config_entries.async_forward_entry_unload(entry, 'climate')
    if config[CONF_DISPLAY_LIGHT] == True:
        await hass.config_entries.async_forward_entry_unload(entry, 'light')
    if config[CONF_CHILD_LOCK] == True:
        await hass.config_entries.async_forward_entry_unload(entry, 'lock')

    return True


async def async_update_entry(hass, entry):
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def setup_device(hass, config):
    device = GoldairTuyaDevice(
        config.get(CONF_NAME),
        config.get(CONF_DEVICE_ID),
        config.get(CONF_HOST),
        config.get(CONF_LOCAL_KEY),
        hass
    )
    hass.data[DOMAIN][config.get(CONF_DEVICE_ID)] = device


def delete_device(hass, config):
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]
