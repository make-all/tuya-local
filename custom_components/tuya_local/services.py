"""Services for Tuya Local integration."""

import asyncio
import logging

import voluptuous as vol
from homeassistant.components import infrared
from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    DEFAULT_DELAY_SECS,
)
from homeassistant.components.remote import DOMAIN as REMOTE_DOMAIN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import service
from homeassistant.util import slugify

from .const import CONF_CALIBRATION, CONF_TYPE, DOMAIN
from .helpers.config import get_device_id
from .helpers.device_config import get_config
from .infrared import TuyaRemoteCommand
from .remote import FLAG_SAVE_DELAY, TuyaLocalRemote

REMOTE_SEND_IR_COMMAND_SCHEMA = {
    vol.Required("emitter_entity_id"): cv.entity_id,
    vol.Required("command"): str,
    vol.Optional("device"): str,
}

SET_CALIBRATION_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("offset"): vol.Coerce(float),
        vol.Optional("attribute"): cv.string,
    }
)

# Read-only measurement dps that may be calibrated, per entity platform.
# The first entry is the default when no "attribute" is given. Settable
# dps are deliberately excluded: HA validates writes against uncalibrated
# entity bounds and device configs use raw values in cross-dp conditions,
# so offsetting writes would corrupt both.
CALIBRATABLE_DPS = {
    "climate": ("current_temperature", "current_humidity"),
    "humidifier": ("current_humidity",),
    "sensor": ("sensor",),
    "water_heater": ("current_temperature",),
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant, entities: list[str]):
    """Set up per-entry services for the Tuya Local integration."""
    if "remote" in entities:
        service.async_register_platform_entity_service(
            hass,
            DOMAIN,
            "send_learned_ir_command",
            entity_domain=REMOTE_DOMAIN,
            schema=REMOTE_SEND_IR_COMMAND_SCHEMA,
            func=async_handle_send_ir_command,
        )
    return True


def async_register_calibration_service(hass: HomeAssistant):
    """Register the set_calibration service (idempotent).

    Registered from async_setup rather than entry setup, as it needs no
    entry state and should exist independently of entry lifecycles.
    """
    if hass.services.has_service(DOMAIN, "set_calibration"):
        return

    async def _set_calibration(call: ServiceCall):
        await async_handle_set_calibration(hass, call)

    hass.services.async_register(
        DOMAIN,
        "set_calibration",
        _set_calibration,
        schema=SET_CALIBRATION_SCHEMA,
    )


async def async_handle_set_calibration(hass: HomeAssistant, call: ServiceCall):
    """Set a calibration offset for a reading of a tuya-local entity.

    The offset is stored in the config entry options and applied by the dp
    value pipeline, so it survives restarts and applies only to this device
    instance even when several devices share the same config file.
    """
    entity_id = call.data["entity_id"]
    offset = call.data["offset"]

    registry = er.async_get(hass)
    reg_entry = registry.async_get(entity_id)
    if reg_entry is None or reg_entry.platform != DOMAIN:
        raise ServiceValidationError(f"{entity_id} is not a tuya_local entity")
    entry = hass.config_entries.async_get_entry(reg_entry.config_entry_id)
    if entry is None:
        raise ServiceValidationError(f"Config entry for {entity_id} not found")

    domain = entity_id.split(".")[0]
    allowed = CALIBRATABLE_DPS.get(domain)
    if not allowed:
        raise ServiceValidationError(
            f"{domain} entities cannot be calibrated; only measurement "
            "readings of sensor, climate, humidifier and water_heater "
            "entities can"
        )
    dp_name = call.data.get("attribute") or allowed[0]
    if dp_name not in allowed:
        raise ServiceValidationError(
            f"'{dp_name}' cannot be calibrated; valid attributes for "
            f"{domain}: {', '.join(allowed)}"
        )

    device_uid = get_device_id(entry.data)
    prefix = f"{device_uid}-"
    if not reg_entry.unique_id.startswith(prefix):
        raise ServiceValidationError(f"Unexpected unique id for {entity_id}")
    entity_key = reg_entry.unique_id.removeprefix(prefix)

    conf_type = entry.data.get(CONF_TYPE)
    device_conf = (
        await hass.async_add_executor_job(get_config, conf_type) if conf_type else None
    )
    if device_conf is None:
        raise ServiceValidationError(
            f"The device config for {entity_id} could not be loaded"
        )
    matched = None
    for e in device_conf.all_entities():
        if slugify(e.config_id) == entity_key:
            matched = e
            break
    if matched is None:
        raise ServiceValidationError(
            f"{entity_id} does not match any entity of its device config "
            "(possibly a legacy entity created before entity ids were "
            "standardised)"
        )
    target = matched.find_dps(dp_name)
    if target is None:
        raise ServiceValidationError(
            f"{entity_id} has no '{dp_name}' reading to calibrate"
        )
    if target.type not in (int, float) or target.rawtype in ("bitfield", "unixtime"):
        raise ServiceValidationError(
            f"'{dp_name}' of {entity_id} is not a calibratable numeric reading"
        )

    calibration = dict(entry.options.get(CONF_CALIBRATION, {}))
    key = f"{entity_key}/{dp_name}"
    if offset == 0:
        calibration.pop(key, None)
        _LOGGER.info("Removing calibration of %s for %s", dp_name, entity_id)
    else:
        calibration[key] = offset
        _LOGGER.info("Calibrating %s of %s by %+g", dp_name, entity_id, offset)
    # The entry's update listener normally reloads it, applying the new
    # offsets — but that listener is only registered while the entry is
    # fully set up. If an update landed while a reload was in flight,
    # schedule one ourselves so the change is not silently lost.
    changed = hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_CALIBRATION: calibration}
    )
    if changed and not entry.update_listeners:
        hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_handle_send_ir_command(entity, call: ServiceCall):
    """Action to send a saved remote command."""
    _LOGGER.info("Sending saved remote command: %s", call.data)

    if not isinstance(entity, TuyaLocalRemote):
        raise ValueError("Entity must be a tuya-local remote")
    if not entity._storage_loaded:
        await entity._async_load_storage()

    emitter = call.data.get("emitter_entity_id")
    device = call.data.get("device")
    command = call.data.get("command")
    delay = call.data.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
    code_list = entity._extract_codes(
        [command], subdevice=device
    )  # Validate command and get code
    at_least_one_sent = False
    for codes in code_list:
        if at_least_one_sent:
            await asyncio.sleep(delay)
        if len(codes) > 1:
            code = codes[entity._flags[device]]
            entity._flags[device] ^= 1
        else:
            code = codes[0]
        if code.startswith("rf:"):
            _LOGGER.error("RF emitters are not yet supported by this service")
            continue
        await infrared.async_send_command(
            entity.hass, emitter, TuyaRemoteCommand(code=code)
        )
        at_least_one_sent = True

        if at_least_one_sent:
            entity._flag_storage.async_delay_save(
                lambda: entity._flags, FLAG_SAVE_DELAY
            )
