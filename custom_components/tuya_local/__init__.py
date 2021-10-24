"""
Platform for Tuya WiFi-connected devices.

Based on nikrolls/homeassistant-goldair-climate for Goldair branded devices.
Based on sean6541/tuya-homeassistant for service call logic, and TarxBoy's
investigation into Goldair's tuyapi statuses
https://github.com/codetheweb/tuyapi/issues/31.
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_migrate_entries

from .const import (
    CONF_DEVICE_ID,
    CONF_LIGHT,
    CONF_LOCAL_KEY,
    CONF_LOCK,
    CONF_TYPE,
    DOMAIN,
)
from .device import setup_device, delete_device
from .helpers.device_config import get_config

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass, entry: ConfigEntry):
    """Migrate to latest config format."""

    CONF_TYPE_AUTO = "auto"
    CONF_DISPLAY_LIGHT = "display_light"
    CONF_CHILD_LOCK = "child_lock"

    if entry.version == 1:
        # Removal of Auto detection.
        config = {**entry.data, **entry.options, "name": entry.title}
        opts = {**entry.options}
        if config[CONF_TYPE] == CONF_TYPE_AUTO:
            device = setup_device(hass, config)
            config[CONF_TYPE] = await device.async_inferred_type()
            if config[CONF_TYPE] is None:
                _LOGGER.error(
                    f"Unable to determine type for device {config[CONF_DEVICE_ID]}."
                )
                return False

        entry.data = {
            CONF_DEVICE_ID: config[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
            CONF_HOST: config[CONF_HOST],
        }
        if CONF_CHILD_LOCK in config:
            opts.pop(CONF_CHILD_LOCK, False)
            opts[CONF_LOCK] = config[CONF_CHILD_LOCK]
        if CONF_DISPLAY_LIGHT in config:
            opts.pop(CONF_DISPLAY_LIGHT, False)
            opts[CONF_LIGHT] = config[CONF_DISPLAY_LIGHT]

        entry.options = {**opts}
        entry.version = 2

    if entry.version == 2:
        # CONF_TYPE is not configurable, move it from options to the main config.
        config = {**entry.data, **entry.options, "name": entry.title}
        opts = {**entry.options}
        # Ensure type has been migrated.  Some users are reporting errors which
        # suggest it was removed completely.  But that is probably due to
        # overwriting options without CONF_TYPE.
        if config.get(CONF_TYPE, CONF_TYPE_AUTO) == CONF_TYPE_AUTO:
            device = setup_device(hass, config)
            config[CONF_TYPE] = await device.async_inferred_type()
            if config[CONF_TYPE] is None:
                _LOGGER.error(
                    f"Unable to determine type for device {config[CONF_DEVICE_ID]}."
                )
                return False
        entry.data = {
            CONF_DEVICE_ID: config[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
            CONF_HOST: config[CONF_HOST],
            CONF_TYPE: config[CONF_TYPE],
        }
        opts.pop(CONF_TYPE, None)
        entry.options = {**opts}
        entry.version = 3

    if entry.version == 3:
        # Migrate to filename based config_type, to avoid needing to
        # parse config files to find the right one.
        config = {**entry.data, **entry.options, "name": entry.title}
        config_type = get_config(config[CONF_TYPE]).config_type

        # Special case for kogan_switch.  Consider also v2.
        if config_type == "smartplugv1":
            device = setup_device(hass, config)
            config_type = await device.async_inferred_type()
            if config_type != "smartplugv2":
                config_type = "smartplugv1"

        entry.data = {
            CONF_DEVICE_ID: config[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
            CONF_HOST: config[CONF_HOST],
            CONF_TYPE: config_type,
        }
        entry.version = 4

    if entry.version == 4:
        # Migrate indexes to entity id rather than type, to allow for multiple
        # entities of the same type for a device.
        config = {**entry.data, **entry.options, "name": entry.title}
        devcfg = get_config(config[CONF_TYPE])
        opts = {**entry.options}
        newopts = {**opts}
        entry.data = {
            CONF_DEVICE_ID: config[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
            CONF_HOST: config[CONF_HOST],
            CONF_TYPE: config[CONF_TYPE],
        }
        e = devcfg.primary_entity
        if e.config_id != e.entity:
            newopts.pop(e.entity, None)
            newopts[e.config_id] = opts.get(e.entity, False)

        for e in devcfg.secondary_entities():
            if e.config_id != e.entity:
                newopts.pop(e.entity, None)
                newopts[e.config_id] = opts.get(e.entity, False)

        entry.options = {**newopts}
        entry.version = 5

    if entry.version == 5:
        # Migrate unique ids of existing entities to new format
        old_id = entry.unique_id
        conf_file = get_config(entry.data[CONF_TYPE])
        if conf_file is None:
            _LOGGER.error(f"Configuration file for {entry.data[CONF_TYPE]} not found.")
            return False

        @callback
        def update_unique_id(entity_entry):
            """Update the unique id of an entity entry."""
            e = conf_file.primary_entity
            if e.entity != entity_entry.platform:
                for e in conf_file.secondary_entities():
                    if e.entity == entity_entry.platform:
                        break
            if e.entity == entity_entry.platform:
                new_id = e.unique_id(old_id)
                if new_id != old_id:
                    _LOGGER.info(
                        f"Migrating {e.entity} unique_id {old_id} to {new_id}."
                    )
                    return {
                        "new_unique_id": entity_entry.unique_id.replace(old_id, new_id)
                    }

        await async_migrate_entries(hass, entry.entry_id, update_unique_id)
        entry.version = 6

    if entry.version == 6:
        # Migrate some entity names to make them consistent for translations
        opts = {**entry.data, **entry.options}
        newopts = {**entry.options}
        master = opts.get("switch_main_switch")
        if master is not None:
            newopts.pop("switch_main_switch", None)
            newopts["switch_master"] = master
        outlet1 = opts.get("switch_left_outlet")
        outlet2 = opts.get("switch_right_outlet")
        outlet1 = opts.get("switch_wall_switch_1") if outlet1 is None else outlet1
        outlet2 = opts.get("switch_wall_switch_2") if outlet2 is None else outlet2
        if outlet1 is not None:
            newopts.pop("switch_left_outlet", None)
            newopts.pop("switch_wall_switch_1", None)
            newopts["switch_outlet_1"] = outlet1
        if outlet2 is not None:
            newopts.pop("switch_right_outlet", None)
            newopts.pop("switch_wall_switch_2", None)
            newopts["switch_outlet_2"] = outlet2

        entry.options = {**newopts}
        entry.version = 7

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(f"Setting up entry for device: {entry.data[CONF_DEVICE_ID]}")
    config = {**entry.data, **entry.options, "name": entry.title}
    setup_device(hass, config)
    device_conf = get_config(entry.data[CONF_TYPE])
    if device_conf is None:
        _LOGGER.error(f"Configuration file for {config[CONF_TYPE]} not found.")
        return False

    entities = {}
    e = device_conf.primary_entity
    if config.get(e.config_id, False):
        entities[e.entity] = True
    for e in device_conf.secondary_entities():
        if config.get(e.config_id, False):
            entities[e.entity] = True

    for e in entities:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, e))

    entry.add_update_listener(async_update_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(f"Unloading entry for device: {entry.data[CONF_DEVICE_ID]}")
    config = entry.data
    data = hass.data[DOMAIN][config[CONF_DEVICE_ID]]
    device_conf = get_config(config[CONF_TYPE])
    if device_conf is None:
        _LOGGER.error(f"Configuration file for {config[CONF_TYPE]} not found.")
        return False

    entities = {}
    e = device_conf.primary_entity
    if e.config_id in data:
        entities[e.entity] = True
    for e in device_conf.secondary_entities():
        if e.config_id in data:
            entities[e.entity] = True

    for e in entities:
        await hass.config_entries.async_forward_entry_unload(entry, e)

    delete_device(hass, config)
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(f"Updating entry for device: {entry.data[CONF_DEVICE_ID]}")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
