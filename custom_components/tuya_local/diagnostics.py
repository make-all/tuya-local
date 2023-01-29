"""Diagnostics support for tuya-local."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import REDACTED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .const import (
    API_PROTOCOL_VERSIONS,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from .device import TuyaLocalDevice


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return _async_get_diagnostics(hass, entry)


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    return _async_get_diagnostics(hass, entry, device)


@callback
def _async_get_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: DeviceEntry | None = None,
) -> dict[str, Any]:
    """Return diagnostics for a tuya-local config entry."""
    hass_data = hass.data[DOMAIN][entry.data["device_id"]]

    data = {
        "name": entry.title,
        "type": entry.data[CONF_TYPE],
        "device_id": REDACTED,
        "local_key": REDACTED,
        "host": REDACTED,
        "protocol_version": entry.data[CONF_PROTOCOL_VERSION],
    }

    # The DeviceEntry also has interesting looking data, but this
    # integration does not publish anything to it other than some hardcoded
    # values that don't change between devices. Instead get the live data
    # from the running hass.
    data |= _async_device_as_dict(hass, hass_data["device"])

    return data


@callback
def _async_device_as_dict(
    hass: HomeAssistant, device: TuyaLocalDevice
) -> dict[str, Any]:
    """Represent a Tuya Local devcie as a dictionary."""

    # Base device information, without sensitive information
    data = {
        "name": device.name,
        "api_version_set": device._api.version,
        "api_version_used": API_PROTOCOL_VERSIONS[device._api_protocol_version_index],
        "api_working": device._api_protocol_working,
        "status": device._api.dps_cache,
        "cached_state": device._cached_state,
        "pending_state": device._pending_updates,
        "connected": device._running,
    }

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    hass_device = device_registry.async_get_device(
        identifiers={(DOMAIN, device.unique_id)}
    )
    if hass_device:
        data["home_assistant"] = {
            "name": hass_device.name,
            "name_by_user": hass_device.name_by_user,
            "disabled": hass_device.disabled,
            "disabled_by": hass_device.disabled_by,
            "entities": [],
        }

        hass_entities = er.async_entries_for_device(
            entity_registry,
            device_id=hass_device.id,
            include_disabled_entities=True,
        )
        for entity_entry in hass_entities:
            state = hass.states.get(entity_entry.entity_id)
            state_dict = None
            if state:
                state_dict = dict(state.as_dict())

                # Redact entity_picture in case it is sensitive
                if "entity_picture" in state_dict["attributes"]:
                    state_dict["attributes"] = {
                        **state_dict["attributes"],
                        "entity_picture": REDACTED,
                    }
                # Context is not useful information
                state_dict.pop("context", None)

            data["home_assistant"]["entities"].append(
                {
                    "disabled": entity_entry.disabled,
                    "disabled_by": entity_entry.disabled_by,
                    "entity_category": entity_entry.entity_category,
                    "device_class": entity_entry.device_class,
                    "original_device_class": entity_entry.original_device_class,
                    "icon": entity_entry.icon,
                    "unit_of_measurement": entity_entry.unit_of_measurement,
                    "state": state_dict,
                }
            )
    return data
