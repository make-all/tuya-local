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
from homeassistant.exceptions import ConfigEntryNotReady
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
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
                CONF_HOST: config[CONF_HOST],
            },
            version=2,
        )

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
        opts.pop(CONF_TYPE, None)
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
                CONF_HOST: config[CONF_HOST],
                CONF_TYPE: config[CONF_TYPE],
            },
            options={**opts},
            version=3,
        )

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
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_LOCAL_KEY: config[CONF_LOCAL_KEY],
                CONF_HOST: config[CONF_HOST],
                CONF_TYPE: config_type,
            },
            version=4,
        )

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
        hass.config_entries.async_update_entry(entry, version=6)

    if entry.version <= 8:
        # Deprecated entities are removed, trim the config back to required
        # config only
        conf = {**entry.data, **entry.options}
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_DEVICE_ID: conf[CONF_DEVICE_ID],
                CONF_LOCAL_KEY: conf[CONF_LOCAL_KEY],
                CONF_HOST: conf[CONF_HOST],
                CONF_TYPE: conf[CONF_TYPE],
            },
            options={},
            version=9,
        )

    if entry.version <= 9:
        # Added protocol_version, default to auto
        conf = {**entry.data, **entry.options}
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_DEVICE_ID: conf[CONF_DEVICE_ID],
                CONF_LOCAL_KEY: conf[CONF_LOCAL_KEY],
                CONF_HOST: conf[CONF_HOST],
                CONF_TYPE: conf[CONF_TYPE],
                CONF_PROTOCOL_VERSION: "auto",
            },
            options={},
            version=10,
        )

    if entry.version <= 10:
        conf = entry.data | entry.options
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_DEVICE_ID: conf[CONF_DEVICE_ID],
                CONF_LOCAL_KEY: conf[CONF_LOCAL_KEY],
                CONF_HOST: conf[CONF_HOST],
                CONF_TYPE: conf[CONF_TYPE],
                CONF_PROTOCOL_VERSION: conf[CONF_PROTOCOL_VERSION],
                CONF_POLL_ONLY: False,
            },
            options={},
            version=11,
        )

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
        hass.config_entries.async_update_entry(entry, version=12)

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
        hass.config_entries.async_update_entry(entry, version=13)

    if entry.version == 13 and entry.minor_version < 2:
        # Migrate unique ids of existing entities to new id taking into
        # account translation_key, and standardising naming
        device_id = entry.unique_id
        conf_file = get_config(entry.data[CONF_TYPE])
        if conf_file is None:
            _LOGGER.error(
                NOT_FOUND,
                entry.data[CONF_TYPE],
            )
            return False

        @callback
        def update_unique_id13_2(entity_entry):
            """Update the unique id of an entity entry."""
            old_id = entity_entry.unique_id
            platform = entity_entry.entity_id.split(".", 1)[0]
            # Standardistion of entity naming to use translation_key
            replacements = {
                # special meaning of None to handle _full and _empty variants
                "binary_sensor_tank": None,
                "binary_sensor_tank_full_or_missing": "binary_sensor_tank_full",
                "binary_sensor_water_tank_full": "binary_sensor_tank_full",
                "binary_sensor_low_water": "binary_sensor_tank_empty",
                "binary_sensor_water_tank_empty": "binary_sensor_tank_empty",
                "binary_sensor_fault": "binary_sensor_problem",
                "binary_sensor_error": "binary_sensor_problem",
                "binary_sensor_fault_alarm": "binary_sensor_problem",
                "binary_sensor_errors": "binary_sensor_problem",
                "binary_sensor_defrosting": "binary_sensor_defrost",
                "binary_sensor_anti_frost": "binary_sensor_defrost",
                "binary_sensor_anti_freeze": "binary_sensor_defrost",
                "binary_sensor_low_battery": "binary_sensor_battery",
                "binary_sensor_low_battery_alarm": "binary_sensor_battery",
                "select_temperature_units": "select_temperature_unit",
                "select_display_temperature_unit": "select_temperature_unit",
                "select_display_unit": "select_temperature_unit",
                "select_display_units": "select_temperature_unit",
                "select_temperature_display_units": "select_temperature_unit",
                "switch_defrost": "switch_anti_frost",
                "switch_frost_protection": "switch_anti_frost",
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
                        if (new_suffix and new_id.endswith(new_suffix)) or (
                            new_suffix is None and suffix in new_id
                        ):
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

        await async_migrate_entries(hass, entry.entry_id, update_unique_id13_2)
        hass.config_entries.async_update_entry(entry, minor_version=2)

    if entry.version == 13 and entry.minor_version < 3:
        # Migrate unique ids of existing entities to new id taking into
        # account translation_key, and standardising naming
        device_id = entry.unique_id
        conf_file = get_config(entry.data[CONF_TYPE])
        if conf_file is None:
            _LOGGER.error(
                NOT_FOUND,
                entry.data[CONF_TYPE],
            )
            return False

        @callback
        def update_unique_id13_3(entity_entry):
            """Update the unique id of an entity entry."""
            old_id = entity_entry.unique_id
            platform = entity_entry.entity_id.split(".", 1)[0]
            # Standardistion of entity naming to use translation_key
            replacements = {
                "light_front_display": "light_display",
                "light_lcd_brightness": "light_display",
                "light_coal_bed": "light_logs",
                "light_ember": "light_embers",
                "light_led_indicator": "light_indicator",
                "light_status_indicator": "light_indicator",
                "light_indicator_light": "light_indicator",
                "light_indicators": "light_indicator",
                "light_night_light": "light_nightlight",
                "number_tiemout_period": "number_timeout_period",
                "sensor_remaining_time": "sensor_time_remaining",
                "sensor_timer_remain": "sensor_time_remaining",
                "sensor_timer": "sensor_time_remaining",
                "sensor_timer_countdown": "sensor_time_remaining",
                "sensor_timer_remaining": "sensor_time_remaining",
                "sensor_time_left": "sensor_time_remaining",
                "sensor_timer_minutes_left": "sensor_time_remaining",
                "sensor_timer_time_left": "sensor_time_remaining",
                "sensor_auto_shutoff_time_remaining": "sensor_time_remaining",
                "sensor_warm_time_remaining": "sensor_time_remaining",
                "sensor_run_time_remaining": "sensor_time_remaining",
                "switch_ioniser": "switch_ionizer",
                "switch_run_uv_cycle": "switch_uv_sterilization",
                "switch_uv_light": "switch_uv_sterilization",
                "switch_ihealth": "switch_uv_sterilization",
                "switch_uv_lamp": "switch_uv_sterilization",
                "switch_anti_freeze": "switch_anti_frost",
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
                        if new_suffix and new_id.endswith(new_suffix):
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

        await async_migrate_entries(hass, entry.entry_id, update_unique_id13_3)
        hass.config_entries.async_update_entry(entry, minor_version=3)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(
        "Setting up entry for device: %s",
        get_device_id(entry.data),
    )
    config = {**entry.data, **entry.options, "name": entry.title}
    try:
        setup_device(hass, config)
    except Exception as e:
        raise ConfigEntryNotReady("tuya-local device not ready") from e

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
