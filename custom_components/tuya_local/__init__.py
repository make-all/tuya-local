"""
Platform for Tuya WiFi-connected devices.

Based on nikrolls/homeassistant-goldair-climate for Goldair branded devices.
Based on sean6541/tuya-homeassistant for service call logic, and TarxBoy's
investigation into Goldair's tuyapi statuses
https://github.com/codetheweb/tuyapi/issues/31.
"""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .configuration import individual_config_schema
from .const import (
    CONF_CHILD_LOCK,
    CONF_CLIMATE,
    CONF_DEVICE_ID,
    CONF_DISPLAY_LIGHT,
    CONF_LOCAL_KEY,
    CONF_SWITCH,
    DOMAIN,
)
from .device import TuyaLocalDevice
from .config_flow import ConfigFlowHandler

_LOGGER = logging.getLogger(__name__)

VERSION = "0.1.2"

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.Schema(individual_config_schema())])},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    for device_config in config.get(DOMAIN, []):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=device_config
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(f"Setting up entry for device: {entry.data[CONF_DEVICE_ID]}")
    config = {**entry.data, **entry.options, "name": entry.title}
    setup_device(hass, config)

    if config[CONF_CLIMATE] is True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "climate")
        )
    if config[CONF_DISPLAY_LIGHT] is True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "light")
        )
    if config[CONF_CHILD_LOCK] is True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "lock")
        )
    if config[CONF_SWITCH] is True:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "switch")
        )
    entry.add_update_listener(async_update_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    if entry.data.get(SOURCE_IMPORT):
        raise ValueError("Devices configured via yaml cannot be deleted from the UI.")

    _LOGGER.debug(f"Unloading entry for device: {entry.data[CONF_DEVICE_ID]}")
    config = entry.data
    data = hass.data[DOMAIN][config[CONF_DEVICE_ID]]

    if CONF_CLIMATE in data:
        await hass.config_entries.async_forward_entry_unload(entry, "climate")
    if CONF_DISPLAY_LIGHT in data:
        await hass.config_entries.async_forward_entry_unload(entry, "light")
    if CONF_CHILD_LOCK in data:
        await hass.config_entries.async_forward_entry_unload(entry, "lock")
    if CONF_SWITCH in data:
        await hass.config_entries.async_forward_entry_unload(entry, "switch")

    delete_device(hass, config)
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry):
    if entry.data.get(SOURCE_IMPORT):
        raise ValueError("Devices configured via yaml cannot be updated from the UI.")

    _LOGGER.debug(f"Updating entry for device: {entry.data[CONF_DEVICE_ID]}")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def setup_device(hass: HomeAssistant, config: dict):
    _LOGGER.debug(f"Creating device: {config[CONF_DEVICE_ID]}")
    hass.data[DOMAIN] = hass.data.get(DOMAIN, {})
    device = TuyaLocalDevice(
        config[CONF_NAME],
        config[CONF_DEVICE_ID],
        config[CONF_HOST],
        config[CONF_LOCAL_KEY],
        hass,
    )
    hass.data[DOMAIN][config[CONF_DEVICE_ID]] = {"device": device}

    return device


def delete_device(hass: HomeAssistant, config: dict):
    _LOGGER.debug(f"Deleting device: {config[CONF_DEVICE_ID]}")
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]["device"]
