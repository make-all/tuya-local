"""
Platform for Goldair WiFi-connected heaters and panels.

Based on sean6541/tuya-homeassistant for service call logic, and TarxBoy's
investigation into Goldair's tuyapi statuses
https://github.com/codetheweb/tuyapi/issues/31.
"""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .configuration import individual_config_schema
from .const import (DOMAIN, CONF_CHILD_LOCK, CONF_CLIMATE, CONF_DEVICE_ID,
                    CONF_DISPLAY_LIGHT, CONF_LOCAL_KEY, CONF_TYPE,
                    CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN, CONF_TYPE_HEATER, SCAN_INTERVAL)
from .device import GoldairTuyaDevice

_LOGGER = logging.getLogger(__name__)

VERSION = "0.0.8"

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.Schema(individual_config_schema())])},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    hass.data[DOMAIN] = {}

    for device_config in config.get(DOMAIN, []):
        setup_device(hass, device_config)

        discovery_info = {
            CONF_DEVICE_ID: device_config[CONF_DEVICE_ID],
            CONF_TYPE: device_config[CONF_TYPE],
        }

        if device_config[CONF_CLIMATE] == True:
            hass.async_create_task(
                async_load_platform(hass, "climate", DOMAIN, discovery_info, config)
            )
        if device_config[CONF_DISPLAY_LIGHT] == True:
            hass.async_create_task(
                async_load_platform(hass, "light", DOMAIN, discovery_info, config)
            )
        if device_config[CONF_CHILD_LOCK] == True:
            hass.async_create_task(
                async_load_platform(hass, "lock", DOMAIN, discovery_info, config)
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    config = {**entry.data, **entry.options, 'name': entry.title}
    setup_device(hass, config)

    if config[CONF_CLIMATE] == True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "climate")
        )
    if config[CONF_DISPLAY_LIGHT] == True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "light")
        )
    if config[CONF_CHILD_LOCK] == True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "lock")
        )

    entry.add_update_listener(async_update_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    config = entry.data
    data = hass.data[DOMAIN][config[CONF_DEVICE_ID]]

    if CONF_CLIMATE in data:
        await hass.config_entries.async_forward_entry_unload(entry, "climate")
    if CONF_DISPLAY_LIGHT in data:
        await hass.config_entries.async_forward_entry_unload(entry, "light")
    if CONF_CHILD_LOCK in data:
        await hass.config_entries.async_forward_entry_unload(entry, "lock")

    delete_device(hass, config)
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry):
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def setup_device(hass: HomeAssistant, config: dict):
    device = GoldairTuyaDevice(
        config[CONF_NAME],
        config[CONF_DEVICE_ID],
        config[CONF_HOST],
        config[CONF_LOCAL_KEY],
        hass,
    )
    hass.data[DOMAIN][config[CONF_DEVICE_ID]] = {
        'device': device
    }


def delete_device(hass: HomeAssistant, config: dict):
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]['device']
