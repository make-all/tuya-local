"""IP address management for Tuya Local devices."""

import asyncio
import logging
from datetime import timedelta
from typing import Dict, Optional, Set

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .device_scanner import scan_for_device

_LOGGER = logging.getLogger(__name__)

# How often to check for IP changes (in minutes)
IP_CHECK_INTERVAL = 30

# How many consecutive failures before attempting IP update
FAILURE_THRESHOLD = 3

# Track devices that are having communication issues
_failing_devices: Dict[str, int] = {}
_ip_update_tasks: Set[str] = set()


class IPManager:
    """Manages automatic IP address updates for Tuya devices."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the IP manager."""
        self.hass = hass
        self._unsub_timer = None
        self._device_ips: Dict[str, str] = {}

    async def start(self):
        """Start the IP manager."""
        if self._unsub_timer is None:
            self._unsub_timer = async_track_time_interval(
                self.hass,
                self._check_device_ips,
                interval=timedelta(minutes=IP_CHECK_INTERVAL),
            )
            _LOGGER.info("Started IP manager for automatic device discovery")

    async def stop(self):
        """Stop the IP manager."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
            _LOGGER.info("Stopped IP manager")

    def report_device_failure(self, device_id: str):
        """Report that a device communication failed."""
        _failing_devices[device_id] = _failing_devices.get(device_id, 0) + 1
        failure_count = _failing_devices[device_id]
        _LOGGER.debug(
            "Device %s failure count: %d (threshold: %d)",
            device_id,
            failure_count,
            FAILURE_THRESHOLD,
        )

        if failure_count >= FAILURE_THRESHOLD:
            _LOGGER.info(
                "Device %s has reached failure threshold (%d), will be scanned for IP update",
                device_id,
                FAILURE_THRESHOLD,
            )

    def report_device_success(self, device_id: str):
        """Report that a device communication succeeded."""
        if device_id in _failing_devices:
            failure_count = _failing_devices[device_id]
            _LOGGER.info(
                "Device %s communication restored (was at %d failures)",
                device_id,
                failure_count,
            )
            del _failing_devices[device_id]
        else:
            _LOGGER.debug("Device %s communication successful", device_id)

    async def _check_device_ips(self, now=None):
        """Check for devices that need IP updates."""
        _LOGGER.debug("Checking for devices that need IP updates")

        # Get all Tuya Local config entries
        entries = [
            entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if not entry.disabled_by
        ]

        _LOGGER.debug("Found %d Tuya Local devices", len(entries))

        for entry in entries:
            device_id = entry.data.get(CONF_DEVICE_ID)
            if not device_id:
                continue

            # Check if this device is having communication issues
            failure_count = _failing_devices.get(device_id, 0)
            _LOGGER.debug("Device %s failure count: %d", device_id, failure_count)

            if failure_count >= FAILURE_THRESHOLD:
                # Avoid duplicate IP update tasks
                if device_id not in _ip_update_tasks:
                    _LOGGER.info("Starting IP update task for device %s", device_id)
                    _ip_update_tasks.add(device_id)
                    asyncio.create_task(self._update_device_ip(entry, device_id))
                else:
                    _LOGGER.debug(
                        "IP update already in progress for device %s", device_id
                    )

    async def _update_device_ip(self, entry: ConfigEntry, device_id: str):
        """Update the IP address for a specific device."""
        try:
            _LOGGER.info("Attempting to find new IP for device %s", device_id)

            # Scan for the device
            local_device = await self.hass.async_add_executor_job(
                scan_for_device, device_id
            )

            if local_device and local_device.get("ip"):
                new_ip = local_device.get("ip")
                current_ip = entry.data.get(CONF_HOST, "")

                if new_ip != current_ip:
                    _LOGGER.info(
                        "Found new IP %s for device %s (was %s)",
                        new_ip,
                        device_id,
                        current_ip,
                    )

                    # Update the configuration entry
                    await self._update_config_entry(entry, new_ip)

                    # Clear the failure count
                    if device_id in _failing_devices:
                        del _failing_devices[device_id]

                    # Notify user
                    await self._notify_ip_update(entry, current_ip, new_ip)
                else:
                    _LOGGER.debug("Device %s IP unchanged: %s", device_id, new_ip)
            else:
                _LOGGER.warning("Could not find device %s on network", device_id)

        except Exception as e:
            _LOGGER.error("Error updating IP for device %s: %s", device_id, e)
        finally:
            # Remove from active tasks
            _ip_update_tasks.discard(device_id)

    async def _update_config_entry(self, entry: ConfigEntry, new_ip: str):
        """Update the configuration entry with new IP address."""
        try:
            # Update the entry data
            new_data = {**entry.data, CONF_HOST: new_ip}

            # Update the configuration entry
            self.hass.config_entries.async_update_entry(entry, data=new_data)

            _LOGGER.info(
                "Updated configuration entry for device %s with new IP %s",
                entry.data.get(CONF_DEVICE_ID),
                new_ip,
            )

            # Restart the device to use the new IP
            await self._restart_device(entry)

        except Exception as e:
            _LOGGER.error(
                "Failed to update config entry for device %s: %s",
                entry.data.get(CONF_DEVICE_ID),
                e,
            )

    async def _restart_device(self, entry: ConfigEntry):
        """Restart the device with the new IP address."""
        try:
            # Unload the current device
            await self.hass.config_entries.async_unload(entry.entry_id)

            # Wait a moment for cleanup
            await asyncio.sleep(1)

            # Reload the device with new IP
            await self.hass.config_entries.async_setup(entry.entry_id)

            _LOGGER.info(
                "Restarted device %s with new IP", entry.data.get(CONF_DEVICE_ID)
            )

        except Exception as e:
            _LOGGER.error(
                "Failed to restart device %s: %s", entry.data.get(CONF_DEVICE_ID), e
            )

    async def _notify_ip_update(self, entry: ConfigEntry, old_ip: str, new_ip: str):
        """Send notification about IP update."""
        try:
            device_name = entry.title or entry.data.get(
                CONF_DEVICE_ID, "Unknown Device"
            )

            # Create a persistent notification
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Tuya Local - Device IP Updated",
                    "message": (
                        f"Device '{device_name}' IP address has been automatically updated "
                        f"from {old_ip} to {new_ip}. The device should now be accessible."
                    ),
                    "notification_id": f"tuya_local_ip_update_{entry.data.get(CONF_DEVICE_ID)}",
                },
            )

        except Exception as e:
            _LOGGER.error("Failed to send IP update notification: %s", e)

    @callback
    def get_device_status(self, device_id: str) -> Dict[str, any]:
        """Get the current status of a device."""
        failure_count = _failing_devices.get(device_id, 0)
        is_updating = device_id in _ip_update_tasks

        return {
            "device_id": device_id,
            "failure_count": failure_count,
            "is_updating_ip": is_updating,
            "needs_ip_update": failure_count >= FAILURE_THRESHOLD,
        }


# Global IP manager instance
_ip_manager: Optional[IPManager] = None


async def async_setup_ip_manager(hass: HomeAssistant) -> IPManager:
    """Set up the global IP manager."""
    global _ip_manager
    if _ip_manager is None:
        _ip_manager = IPManager(hass)
        await _ip_manager.start()
    return _ip_manager


async def async_stop_ip_manager():
    """Stop the global IP manager."""
    global _ip_manager
    if _ip_manager:
        await _ip_manager.stop()
        _ip_manager = None


def report_device_failure(device_id: str):
    """Report device communication failure."""
    if _ip_manager:
        _ip_manager.report_device_failure(device_id)


def report_device_success(device_id: str):
    """Report device communication success."""
    if _ip_manager:
        _ip_manager.report_device_success(device_id)


def get_ip_manager() -> Optional[IPManager]:
    """Get the global IP manager instance."""
    return _ip_manager
