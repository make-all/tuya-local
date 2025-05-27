import logging
from typing import Any

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
        # Restore cached authentication
        if cached := self.__hass.data[DOMAIN].get("auth_cache"):
            self.__authentication = cached

    async def async_get_qr_code(self, user_code: str | None = None) -> bool:
        """Get QR code from Tuya server for user code authentication."""
        if not user_code:
            user_code = self.__user_code
            if not user_code:
                _LOGGER.error("Cannot get QR code without a user code")
                return False, {TUYA_RESPONSE_MSG: "QR code requires a user code"}

        response = await self.__hass.async_add_executor_job(
            self.__login_control.qr_code,
            TUYA_CLIENT_ID,
            TUYA_SCHEMA,
            user_code,
        )
        if response.get(TUYA_RESPONSE_SUCCESS, False):
            self.__user_code = user_code
            self.__qr_code = response[TUYA_RESPONSE_RESULT][TUYA_RESPONSE_QR_CODE]
            return self.__qr_code

        _LOGGER.error("Failed to get QR code: %s", response)
        self.__error_code = response.get(TUYA_RESPONSE_CODE, {})
        self.__error_msg = response.get(TUYA_RESPONSE_MSG, "Unknown error")

        return False

    async def async_login(self) -> bool:
        """Login to the Tuya cloud."""
        if not self.__user_code or not self.__qr_code:
            _LOGGER.warning("Login attempted without successful QR scan")
            return False, {}

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
            self.__hass.data[DOMAIN]["auth_cache"] = self.__authentication
        else:
            _LOGGER.warning("Login failed: %s", info)
            self.__error_code = info.get(TUYA_RESPONSE_CODE, {})
            self.__error_msg = info.get(TUYA_RESPONSE_MSG, "Unknown error")

        return success

    async def async_get_devices(self) -> dict[str, Any]:
        """Get all devices associated with the account."""
        token_listener = TokenListener(self.__hass)
        manager = Manager(
            TUYA_CLIENT_ID,
            self.__authentication["user_code"],
            self.__authentication["terminal_id"],
            self.__authentication["endpoint"],
            self.__authentication["token_info"],
            token_listener,
        )

        listener = DeviceListener(self.__hass, manager)
        manager.add_device_listener(listener)

        # Get all devices from Tuya cloud
        await self.__hass.async_add_executor_job(manager.update_device_cache)

        # Register known device IDs
        cloud_devices = {}
        domain_data = self.__hass.data.get(DOMAIN)
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
            }
            _LOGGER.debug("Found device: %s", cloud_device["product_name"])

            existing_id = domain_data.get(cloud_device["id"]) if domain_data else None
            existing_uuid = (
                domain_data.get(cloud_device["uuid"]) if domain_data else None
            )
            existing = existing_id or existing_uuid
            cloud_device["exists"] = existing and existing.get("device")
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

        return cloud_devices

    async def async_get_datamodel(self, device_id) -> dict[str, Any] | None:
        """Get the data model for the specified device (QueryThingsDataModel)."""
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

    @property
    def is_authenticated(self) -> bool:
        """Is the cloud account authenticated?"""
        return True if self.__authentication else False

    @property
    def last_error(self) -> dict[str, Any] | None:
        """The last cloud error code and message, if any."""
        if self.__error_code is not None:
            return {
                TUYA_RESPONSE_MSG: self.__error_msg,
                TUYA_RESPONSE_CODE: self.__error_code,
            }


class DeviceListener(SharingDeviceListener):
    """Device update listener."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
    ):
        self.__hass = hass
        self._manager = manager

    def update_device(
        self,
        device: CustomerDevice,
        updated_status_properties: list[str] | None,
    ) -> None:
        """Device status has updated."""
        _LOGGER.debug(
            "Received update for device %s: %s (properties %s)",
            device.id,
            self._manager.device_map[device.id].status,
            updated_status_properties,
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


class TokenListener(SharingTokenListener):
    """Listener for upstream token updates.
    This is only needed to get some debug output when tokens are refreshed."""

    def __init__(self, hass: HomeAssistant):
        self.__hass = hass

    def update_token(self, token_info: dict[str, Any]) -> None:
        """Update the token information."""
        _LOGGER.debug("Token updated")
