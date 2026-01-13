import logging
import asyncio
import time
from typing import Any
from datetime import timedelta
import json
import os

from homeassistant.core import HomeAssistant
from tuya_sharing import (
    CustomerDevice,
    LoginControl,
    Manager,
    SharingDeviceListener,
    SharingTokenListener,
)

from .const import (
    CONF_DEVICE_CID,
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_LOCAL_KEY,
    CONF_TERMINAL_ID,
    DOMAIN,
    TUYA_CLIENT_ID,
    TUYA_RESPONSE_CODE,
    TUYA_RESPONSE_MSG,
    TUYA_RESPONSE_QR_CODE,
    TUYA_RESPONSE_RESULT,
    TUYA_RESPONSE_SUCCESS,
    TUYA_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

AUTH_CACHE_FILE = "/config/tuya_local_auth_cache.json"

HUB_CATEGORIES = [
    "wgsxj",  # Gateway camera
    "lyqwg",  # Router
    "bywg",  # IoT edge gateway
    "zigbee",  # Gateway
    "wg2",  # Gateway
    "dgnzk",  # Multi-function controller
    "videohub",  # Videohub
    "xnwg",  # Virtual gateway
    "qtyycp",  # Voice gateway composite solution
    "alexa_yywg",  # Gateway with Alexa
    "gywg",  # Industrial gateway
    "cnwg",  # Energy gateway
    "wnykq",  # Smart IR
]

SLEEPY_DEVICE_CATEGORIES = [
    "mc",  # Motion sensors
    "pir",  # PIR sensors
    "door",  # Door/window sensors
    "wsdcg",  # Water leak sensors
    "rqbj",  # Gas detectors
    "ywbj",  # Smoke detectors
    "mcs",  # Magnetic contacts
    "sz",  # Various sensors
    "dgn",  # Doorbell (battery powered)
    "sxj",  # Camera (battery powered)
    "kj",  # Air quality sensors
    "wsdbg",  # Water leak sensors
]


class Cloud:
    """Optional Tuya cloud interface for getting device information."""

    def __init__(self, hass: HomeAssistant):
        self.__login_control = LoginControl()
        self.__authentication = {}
        self.__user_code = None
        self.__qr_code = None
        self.__hass = hass
        self.__error_code = None
        self.__error_msg = None

        # Polling configuration
        self._polling_interval = timedelta(hours=4)  # Poll every 4 hours
        self._last_polling_time = None
        self._polling_task = None
        self._devices_cache = {}  # Devices cache
        self._devices_cache_time = None
        self._cache_validity = timedelta(minutes=30)  # Cache valid for 30 minutes

        # Restore cached authentication from file
        self._load_auth_cache()

    def _save_auth_cache(self):
        """Save authentication data to file."""
        try:
            with open(AUTH_CACHE_FILE, 'w') as f:
                json.dump({
                    'authentication': self.__authentication,
                    'user_code': self.__user_code
                }, f)
            _LOGGER.debug("Authentication cache saved")
        except Exception as e:
            _LOGGER.error("Failed to save auth cache: %s", e)

    def _load_auth_cache(self):
        """Load authentication data from file."""
        try:
            if os.path.exists(AUTH_CACHE_FILE):
                with open(AUTH_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self.__authentication = data.get('authentication', {})
                    self.__user_code = data.get('user_code')
                    _LOGGER.debug("Authentication cache loaded")
        except Exception as e:
            _LOGGER.error("Failed to load auth cache: %s", e)

    def _clear_auth_cache(self):
        """Clear authentication cache file."""
        try:
            if os.path.exists(AUTH_CACHE_FILE):
                os.remove(AUTH_CACHE_FILE)
            self.__authentication = {}
            self.__user_code = None
            _LOGGER.debug("Authentication cache cleared")
        except Exception as e:
            _LOGGER.error("Failed to clear auth cache: %s", e)

    async def async_setup_polling(self):
        """Set up periodic device polling."""
        if not self.is_authenticated:
            return

        # Stop previous polling task if exists
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                _LOGGER.debug("Previous polling task cancelled")

        # Start periodic polling
        self._polling_task = asyncio.create_task(self._polling_loop())
        _LOGGER.info("Started device polling with interval: %s hours",
                    self._polling_interval.total_seconds() / 3600)

    async def _polling_loop(self):
        """Background polling loop."""
        try:
            while True:
                # Wait for the polling interval
                await asyncio.sleep(self._polling_interval.total_seconds())
                await self._refresh_devices()
        except asyncio.CancelledError:
            _LOGGER.debug("Polling task cancelled")
        except Exception as e:
            _LOGGER.error("Error in polling loop: %s", e)
            # Try to restart polling after error
            await asyncio.sleep(300)  # Wait 5 minutes before retry
            if self.is_authenticated:
                await self.async_setup_polling()

    async def _refresh_devices(self):
        """Refresh device list."""
        if not self.is_authenticated:
            return

        try:
            _LOGGER.debug("Performing periodic device refresh")
            devices = await self._get_devices_uncached()
            self._devices_cache = devices
            self._devices_cache_time = time.time()
            self._last_polling_time = time.time()

            # Notify about device status changes
            await self._notify_device_updates(devices)

            _LOGGER.info("Successfully refreshed %s devices", len(devices))

        except Exception as e:
            _LOGGER.error("Failed to refresh devices: %s", e)

    async def _get_devices_uncached(self):
        """Get devices without using cache."""
        if not self.is_authenticated:
            _LOGGER.error("Cannot get devices: not authenticated")
            return {}

        token_listener = TokenListener(self.__hass)
        manager = Manager(
            TUYA_CLIENT_ID,
            self.__authentication["user_code"],
            self.__authentication["terminal_id"],
            self.__authentication["endpoint"],
            self.__authentication["token_info"],
            token_listener,
        )

        listener = DeviceListener(self.__hass, manager, self)
        manager.add_device_listener(listener)

        # Get all devices from Tuya cloud
        await self.__hass.async_add_executor_job(manager.update_device_cache)

        # Register known device IDs
        cloud_devices = {}

        existing_entries = self.__hass.config_entries.async_entries(DOMAIN)
        existing_device_ids = set()

        for entry in existing_entries:
            device_id = entry.data.get(CONF_DEVICE_ID)
            if device_id:
                existing_device_ids.add(device_id)

        _LOGGER.debug("Already registered device IDs in HA: %s", existing_device_ids)

        for device in manager.device_map.values():
            cloud_device = {
                "category": device.category,
                "id": device.id,
                "ip": device.ip,
                CONF_LOCAL_KEY: device.local_key
                if hasattr(device, CONF_LOCAL_KEY)
                else "",
                "name": device.name,
                "node_id": device.node_id if hasattr(device, "node_id") else "",
                "online": device.online,
                "product_id": device.product_id,
                "product_name": device.product_name,
                "uid": device.uid,
                "uuid": device.uuid,
                "support_local": device.support_local,
                CONF_DEVICE_CID: None,
                "version": None,
                "is_hub": (
                    device.category in HUB_CATEGORIES
                    or not hasattr(device, "local_key")
                ),
                "last_update": time.time(),
                "is_sleepy": (
                    device.category in SLEEPY_DEVICE_CATEGORIES or
                    ("battery" in str(device.status).lower() if device.status else False)
                ),
            }
            _LOGGER.debug("Found device: %s (category: %s, sleepy: %s)",
                         cloud_device["product_name"],
                         cloud_device["category"],
                         cloud_device["is_sleepy"])

            cloud_device["exists"] = device.id in existing_device_ids

            if hasattr(device, "node_id"):
                index = "/".join(
                    [
                        cloud_device["id"],
                        cloud_device["node_id"],
                    ]
                )
            else:
                index = cloud_device["id"]
            cloud_devices[index] = cloud_device

        _LOGGER.debug("Total devices found: %s, already registered: %s",
                     len(cloud_devices), len(existing_device_ids))

        return cloud_devices

    async def _notify_device_updates(self, devices):
        """Notify about device updates."""
        # Count online/offline devices
        online_count = sum(1 for d in devices.values() if d.get("online"))
        sleepy_online = sum(1 for d in devices.values()
                           if d.get("online") and d.get("is_sleepy"))

        _LOGGER.debug("Device status: %s online (%s sleepy devices online), %s total",
                     online_count, sleepy_online, len(devices))

    async def async_get_qr_code(self, user_code: str | None = None) -> str | bool:
        """Get QR code from Tuya server for user code authentication."""
        if not user_code:
            user_code = self.__user_code
            if not user_code:
                _LOGGER.error("Cannot get QR code without a user code")
                return False

        try:
            response = await self.__hass.async_add_executor_job(
                self.__login_control.qr_code,
                TUYA_CLIENT_ID,
                TUYA_SCHEMA,
                user_code,
            )
        except Exception as e:
            _LOGGER.error("Network error getting QR code: %s", e)
            self.__error_msg = "Network error"
            return False

        if response.get(TUYA_RESPONSE_SUCCESS, False):
            self.__user_code = user_code
            self.__qr_code = response[TUYA_RESPONSE_RESULT][TUYA_RESPONSE_QR_CODE]
            # Save user code to cache
            self._save_auth_cache()
            return self.__qr_code

        _LOGGER.error("Failed to get QR code: %s", response)
        self.__error_code = response.get(TUYA_RESPONSE_CODE, {})
        self.__error_msg = response.get(TUYA_RESPONSE_MSG, "Unknown error")
        return False

    async def async_login(self) -> bool:
        """Login to the Tuya cloud."""
        if not self.__user_code or not self.__qr_code:
            _LOGGER.warning("Login attempted without successful QR scan")
            return False

        success, info = await self.__hass.async_add_executor_job(
            self.__login_control.login_result,
            self.__qr_code,
            TUYA_CLIENT_ID,
            self.__user_code,
        )
        if success:
            self.__authentication = {
                "user_code": self.__user_code,
                "terminal_id": info[CONF_TERMINAL_ID],
                "endpoint": info[CONF_ENDPOINT],
                "token_info": {
                    "t": info["t"],
                    "uid": info["uid"],
                    "expire_time": info["expire_time"],
                    "access_token": info["access_token"],
                    "refresh_token": info["refresh_token"],
                },
            }
            # Save authentication to file
            self._save_auth_cache()

            # Start polling after successful login
            await self.async_setup_polling()

            _LOGGER.info("Successfully logged in to Tuya cloud")
            return True
        else:
            _LOGGER.warning("Login failed: %s", info)
            self.__error_code = info.get(TUYA_RESPONSE_CODE, {})
            self.__error_msg = info.get(TUYA_RESPONSE_MSG, "Unknown error")
            # Clear invalid authentication
            self._clear_auth_cache()
            return False

    async def async_get_devices(self) -> dict[str, Any]:
        """Get all devices associated with the account (with caching)."""
        if not self.is_authenticated:
            _LOGGER.warning("Cannot get devices: not authenticated")
            return {}

        current_time = time.time()

        # Use cache if it's still valid
        if (self._devices_cache and
            self._devices_cache_time and
            current_time - self._devices_cache_time < self._cache_validity.total_seconds()):
            _LOGGER.debug("Returning cached devices")
            return self._devices_cache.copy()

        # Otherwise refresh cache
        devices = await self._get_devices_uncached()
        self._devices_cache = devices
        self._devices_cache_time = current_time

        available_count = len([d for d in devices.values() if not d.get("exists") and d.get(CONF_LOCAL_KEY)])
        _LOGGER.info("Found %s total devices, %s available for adding",
                     len(devices), available_count)

        return devices

    async def async_get_datamodel(self, device_id) -> dict[str, Any] | None:
        """Get the data model for the specified device."""
        if not self.is_authenticated:
            return None

        token_listener = TokenListener(self.__hass)
        manager = Manager(
            TUYA_CLIENT_ID,
            self.__authentication["user_code"],
            self.__authentication["terminal_id"],
            self.__authentication["endpoint"],
            self.__authentication["token_info"],
            token_listener,
        )
        response = await self.__hass.async_add_executor_job(
            manager.customer_api.get,
            f"/v1.0/m/life/devices/{device_id}/status",
        )
        _LOGGER.debug("Datamodel response: %s", response)
        if response.get("result"):
            response = response["result"]
        transform = []
        for entry in response.get("dpStatusRelationDTOS"):
            if entry["supportLocal"]:
                transform.append(
                    {
                        "id": entry["dpId"],
                        "name": entry["dpCode"],
                        "type": entry["valueType"],
                        "format": entry["valueDesc"],
                        "enumMap": entry["enumMappingMap"],
                    }
                )
        return transform

    def logout(self) -> None:
        """Logout from the Tuya cloud."""
        _LOGGER.debug("Logging out from Tuya cloud")

        # Stop polling task
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            self._polling_task = None

        # Clear caches
        self._devices_cache = {}
        self._devices_cache_time = None
        self._last_polling_time = None

        # Clear authentication cache
        self._clear_auth_cache()

        _LOGGER.info("Logged out from Tuya cloud")

    async def async_refresh_devices(self) -> dict[str, Any]:
        """Force refresh device list."""
        _LOGGER.info("Manual device refresh requested")
        self._devices_cache = {}
        self._devices_cache_time = None
        return await self.async_get_devices()

    async def async_clear_device_cache(self) -> None:
        """Clear the device cache."""
        self._devices_cache = {}
        self._devices_cache_time = None
        _LOGGER.info("Device cache cleared")

    @property
    def is_authenticated(self) -> bool:
        """Is the cloud account authenticated?"""
        return bool(self.__authentication and
                   self.__authentication.get("token_info") and
                   self.__authentication.get("token_info").get("access_token"))

    @property
    def last_error(self) -> dict[str, Any] | None:
        """The last cloud error code and message, if any."""
        if self.__error_code is not None:
            return {
                TUYA_RESPONSE_MSG: self.__error_msg,
                TUYA_RESPONSE_CODE: self.__error_code,
            }

    @property
    def authentication_data(self) -> dict[str, Any]:
        """Get authentication data for external use."""
        return self.__authentication.copy() if self.__authentication else {}

    @property
    def has_user_code(self) -> bool:
        """Check if user code is stored."""
        return bool(self.__user_code)

    @property
    def last_polling_time(self):
        """Time of last device polling."""
        return self._last_polling_time

    @property
    def polling_interval(self):
        """Current polling interval."""
        return self._polling_interval

    async def async_set_polling_interval(self, hours: int = 4):
        """Change polling interval."""
        self._polling_interval = timedelta(hours=hours)
        _LOGGER.info("Polling interval set to %s hours", hours)

        # Restart polling with new interval
        if self.is_authenticated:
            await self.async_setup_polling()


class DeviceListener(SharingDeviceListener):
    """Device update listener with periodic refresh support."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        cloud_instance: Cloud = None,
    ):
        self.__hass = hass
        self._manager = manager
        self._cloud = cloud_instance
        self._device_status_cache = {}

    def update_device(
        self,
        device: CustomerDevice,
        updated_status_properties: list[str] | None,
    ) -> None:
        """Device status has updated."""
        device_id = device.id
        current_time = time.time()

        # Cache device status
        self._device_status_cache[device_id] = {
            "status": self._manager.device_map[device_id].status,
            "last_update": current_time,
            "online": device.online if hasattr(device, "online") else True
        }

        _LOGGER.debug(
            "Received update for device %s: %s (properties %s)",
            device_id,
            self._device_status_cache[device_id]["status"],
            updated_status_properties,
        )

        # If device came online after being offline
        if (device_id in self._device_status_cache and
            hasattr(device, "online") and device.online):

            # Check if device was offline for a long time
            last_update = self._device_status_cache[device_id].get("last_update", 0)
            if current_time - last_update > 3600:  # 1 hour
                _LOGGER.info(
                    "Device %s came back online after being offline",
                    device_id
                )

    def add_device(self, device: CustomerDevice) -> None:
        """A new device has been added."""
        _LOGGER.debug(
            "Received add device %s: %s",
            device.id,
            self._manager.device_map[device.id].status,
        )

    def remove_device(self, device_id: str) -> None:
        """A device has been removed."""
        _LOGGER.debug(
            "Received remove device %s: %s",
            device_id,
            self._manager.device_map[device_id].status,
        )

    def get_device_status(self, device_id: str) -> dict[str, Any]:
        """Get cached device status."""
        return self._device_status_cache.get(device_id, {})


class TokenListener(SharingTokenListener):
    """Listener for upstream token updates."""

    def __init__(self, hass: HomeAssistant):
        self.__hass = hass

    def update_token(self, token_info: dict[str, Any]) -> None:
        """Update the token information."""
        _LOGGER.debug("Token updated")
