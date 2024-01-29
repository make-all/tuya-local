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
from homeassistant.util import slugify

from .const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from .device import async_delete_device, get_device_id, setup_device
from .helpers.device_config import get_config

_LOGGER = logging.getLogger(__name__)
NOT_FOUND = "Configuration file for %s not found"


async def async_migrate_entry(hass, entry: ConfigEntry):
    """Migrate to latest config format."""

    CONF_TYPE_AUTO = "auto"

    if entry.version == 1:
        # Removal of Auto detection.
        config = {**entry.data, **entry.options, "name": entry.title}
        if config[CONF_TYPE] == CONF_TYPE_AUTO:
            device = setup_device(hass, config)
            config[CONF_TYPE] = await device.async_inferred_type()
            if config[CONF_TYPE] is None:
                _LOGGER.error(
                    "Unable to determine type for device %s",
                    config[CONF_DEVICE_ID],
                )
                return False

        entry.data = {
            CONF_DEVICE_ID: config[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
            CONF_HOST: config[CONF_HOST],
        }
        entry.version = 2

    if entry.version == 2:
        # CONF_TYPE is not configurable, move from options to main config.
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
                    "Unable to determine type for device %s",
                    config[CONF_DEVICE_ID],
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

    if entry.version <= 5:
        # Migrate unique ids of existing entities to new format
        old_id = entry.unique_id
        conf_file = get_config(entry.data[CONF_TYPE])
        if conf_file is None:
            _LOGGER.error(NOT_FOUND, entry.data[CONF_TYPE])
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
                        "Migrating %s unique_id %s to %s",
                        e.entity,
                        old_id,
                        new_id,
                    )
                    return {
                        "new_unique_id": entity_entry.unique_id.replace(
                            old_id,
                            new_id,
                        )
                    }

        await async_migrate_entries(hass, entry.entry_id, update_unique_id)
        entry.version = 6

    if entry.version <= 8:
        # Deprecated entities are removed, trim the config back to required
        # config only
        conf = {**entry.data, **entry.options}
        entry.data = {
            CONF_DEVICE_ID: conf[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: conf[CONF_LOCAL_KEY],
            CONF_HOST: conf[CONF_HOST],
            CONF_TYPE: conf[CONF_TYPE],
        }
        entry.options = {}
        entry.version = 9

    if entry.version <= 9:
        # Added protocol_version, default to auto
        conf = {**entry.data, **entry.options}
        entry.data = {
            CONF_DEVICE_ID: conf[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: conf[CONF_LOCAL_KEY],
            CONF_HOST: conf[CONF_HOST],
            CONF_TYPE: conf[CONF_TYPE],
            CONF_PROTOCOL_VERSION: "auto",
        }
        entry.options = {}
        entry.version = 10

    if entry.version <= 10:
        conf = entry.data | entry.options
        entry.data = {
            CONF_DEVICE_ID: conf[CONF_DEVICE_ID],
            CONF_LOCAL_KEY: conf[CONF_LOCAL_KEY],
            CONF_HOST: conf[CONF_HOST],
            CONF_TYPE: conf[CONF_TYPE],
            CONF_PROTOCOL_VERSION: "auto",
            CONF_POLL_ONLY: False,
        }
        entry.options = {}
        entry.version = 11

    if entry.version <= 11:
        # Migrate unique ids of existing entities to new format
        device_id = entry.unique_id
        conf_file = get_config(entry.data[CONF_TYPE])
        if conf_file is None:
            _LOGGER.error(
                NOT_FOUND,
                entry.data[CONF_TYPE],
            )
            return False

        @callback
        def update_unique_id12(entity_entry):
            """Update the unique id of an entity entry."""
            old_id = entity_entry.unique_id
            platform = entity_entry.entity_id.split(".", 1)[0]
            e = conf_file.primary_entity
            if e.name:
                expect_id = f"{device_id}-{slugify(e.name)}"
            else:
                expect_id = device_id
            if e.entity != platform or expect_id != old_id:
                for e in conf_file.secondary_entities():
                    if e.name:
                        expect_id = f"{device_id}-{slugify(e.name)}"
                    else:
                        expect_id = device_id
                    if e.entity == platform and expect_id == old_id:
                        break

            if e.entity == platform and expect_id == old_id:
                new_id = e.unique_id(device_id)
                if new_id != old_id:
                    _LOGGER.info(
                        "Migrating %s unique_id %s to %s",
                        e.entity,
                        old_id,
                        new_id,
                    )
                    return {
                        "new_unique_id": entity_entry.unique_id.replace(
                            old_id,
                            new_id,
                        )
                    }

        await async_migrate_entries(hass, entry.entry_id, update_unique_id12)
        entry.version = 12

    if entry.version <= 12:
        # Migrate unique ids of existing entities to new format taking into
        # account device_class if name is missing.
        device_id = entry.unique_id
        conf_file = get_config(entry.data[CONF_TYPE])
        if conf_file is None:
            _LOGGER.error(
                NOT_FOUND,
                entry.data[CONF_TYPE],
            )
            return False

        @callback
        def update_unique_id13(entity_entry):
            """Update the unique id of an entity entry."""
            old_id = entity_entry.unique_id
            platform = entity_entry.entity_id.split(".", 1)[0]
            # if unique_id ends with platform name, then this may have
            # changed with the addition of device_class.
            if old_id.endswith(platform):
                e = conf_file.primary_entity
                if e.entity != platform or e.name:
                    for e in conf_file.secondary_entities():
                        if e.entity == platform and not e.name:
                            break
                if e.entity == platform and not e.name:
                    new_id = e.unique_id(device_id)
                    if new_id != old_id:
                        _LOGGER.info(
                            "Migrating %s unique_id %s to %s",
                            e.entity,
                            old_id,
                            new_id,
                        )
                        return {
                            "new_unique_id": entity_entry.unique_id.replace(
                                old_id,
                                new_id,
                            )
                        }
            else:
                replacements = {
                    "sensor_co2": "sensor_carbon_dioxide",
                    "sensor_co": "sensor_carbon_monoxide",
                    "sensor_pm2_5": "sensor_pm25",
                    "sensor_pm_10": "sensor_pm10",
                    "sensor_pm_1_0": "sensor_pm1",
                    "sensor_pm_2_5": "sensor_pm25",
                    "sensor_tvoc": "sensor_volatile_organic_compounds",
                    "sensor_current_humidity": "sensor_humidity",
                    "sensor_current_temperature": "sensor_temperature",
                }
                for suffix, new_suffix in replacements.items():
                    if old_id.endswith(suffix):
                        e = conf_file.primary_entity
                        if e.entity != platform or e.name:
                            for e in conf_file.secondary_entities():
                                if e.entity == platform and not e.name:
                                    break
                        if e.entity == platform and not e.name:
                            new_id = e.unique_id(device_id)
                            if new_id.endswith(new_suffix):
                                _LOGGER.info(
                                    "Migrating %s unique_id %s to %s",
                                    e.entity,
                                    old_id,
                                    new_id,
                                )
                                return {
                                    "new_unique_id": entity_entry.unique_id.replace(
                                        old_id,
                                        new_id,
                                    )
                                }

        await async_migrate_entries(hass, entry.entry_id, update_unique_id13)
        entry.version = 13

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(
        "Setting up entry for device: %s",
        get_device_id(entry.data),
    )
    config = {**entry.data, **entry.options, "name": entry.title}
    setup_device(hass, config)
    device_conf = get_config(entry.data[CONF_TYPE])
    if device_conf is None:
        _LOGGER.error(NOT_FOUND, config[CONF_TYPE])
        return False

    entities = set()
    e = device_conf.primary_entity
    entities.add(e.entity)
    for e in device_conf.secondary_entities():
        entities.add(e.entity)

    await hass.config_entries.async_forward_entry_setups(entry, entities)

    entry.add_update_listener(async_update_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Unloading entry for device: %s", get_device_id(entry.data))
    config = entry.data
    data = hass.data[DOMAIN][get_device_id(config)]
    device_conf = get_config(config[CONF_TYPE])
    if device_conf is None:
        _LOGGER.error(NOT_FOUND, config[CONF_TYPE])
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

    await async_delete_device(hass, config)
    del hass.data[DOMAIN][get_device_id(config)]

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Updating entry for device: %s", get_device_id(entry.data))
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
