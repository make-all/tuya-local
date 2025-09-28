"""Services for Tuya Local integration."""

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN
from .ip_manager import get_ip_manager

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_SCAN_DEVICE_IP = "scan_device_ip"
SERVICE_SCAN_ALL_DEVICES = "scan_all_devices"
SERVICE_GET_DEVICE_STATUS = "get_device_status"

SCAN_DEVICE_IP_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
    }
)

SCAN_ALL_DEVICES_SCHEMA = vol.Schema({})

GET_DEVICE_STATUS_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Tuya Local services."""

    async def async_scan_device_ip(call: ServiceCall) -> None:
        """Scan for a specific device's IP address."""
        device_id = call.data["device_id"]

        # Find the config entry for this device
        entry = None
        for config_entry in hass.config_entries.async_entries(DOMAIN):
            if config_entry.data.get("device_id") == device_id:
                entry = config_entry
                break

        if not entry:
            _LOGGER.error("Device %s not found in configuration", device_id)
            return

        ip_manager = get_ip_manager()
        if not ip_manager:
            _LOGGER.error("IP manager not available")
            return

        # Trigger IP update for this device
        await ip_manager._update_device_ip(entry, device_id)

        _LOGGER.info("Triggered IP scan for device %s", device_id)

    async def async_scan_all_devices(call: ServiceCall) -> None:
        """Scan for all devices' IP addresses."""
        ip_manager = get_ip_manager()
        if not ip_manager:
            _LOGGER.error("IP manager not available")
            return

        # Trigger IP check for all devices
        await ip_manager._check_device_ips()

        _LOGGER.info("Triggered IP scan for all devices")

    async def async_get_device_status(call: ServiceCall) -> None:
        """Get the status of devices."""
        ip_manager = get_ip_manager()
        if not ip_manager:
            _LOGGER.error("IP manager not available")
            return

        device_id = call.data.get("device_id")

        if device_id:
            # Get status for specific device
            status = ip_manager.get_device_status(device_id)
            _LOGGER.info("Device %s status: %s", device_id, status)
        else:
            # Get status for all devices
            entries = [
                entry
                for entry in hass.config_entries.async_entries(DOMAIN)
                if not entry.disabled_by
            ]

            for entry in entries:
                dev_id = entry.data.get("device_id")
                if dev_id:
                    status = ip_manager.get_device_status(dev_id)
                    _LOGGER.info("Device %s status: %s", dev_id, status)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_DEVICE_IP,
        async_scan_device_ip,
        schema=SCAN_DEVICE_IP_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_ALL_DEVICES,
        async_scan_all_devices,
        schema=SCAN_ALL_DEVICES_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DEVICE_STATUS,
        async_get_device_status,
        schema=GET_DEVICE_STATUS_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Tuya Local services."""
    hass.services.async_remove(DOMAIN, SERVICE_SCAN_DEVICE_IP)
    hass.services.async_remove(DOMAIN, SERVICE_SCAN_ALL_DEVICES)
    hass.services.async_remove(DOMAIN, SERVICE_GET_DEVICE_STATUS)
