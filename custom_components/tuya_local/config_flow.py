import asyncio
import logging
from collections import OrderedDict
from typing import Any

import tinytuya
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    QrCodeSelector,
    QrCodeSelectorConfig,
    QrErrorCorrectionLevel,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from tuya_sharing import (
    CustomerDevice,
    LoginControl,
    Manager,
    SharingDeviceListener,
    SharingTokenListener,
)

from . import DOMAIN
from .const import (
    API_PROTOCOL_VERSIONS,
    CONF_DEVICE_CID,
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TERMINAL_ID,
    CONF_TYPE,
    CONF_USER_CODE,
    DATA_STORE,
    TUYA_CLIENT_ID,
    TUYA_RESPONSE_CODE,
    TUYA_RESPONSE_MSG,
    TUYA_RESPONSE_QR_CODE,
    TUYA_RESPONSE_RESULT,
    TUYA_RESPONSE_SUCCESS,
    TUYA_SCHEMA,
)
from .device import TuyaLocalDevice
from .helpers.config import get_device_id
from .helpers.device_config import get_config
from .helpers.log import log_json

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 13
    MINOR_VERSION = 3
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    device = None
    data = {}

    __user_code: str
    __qr_code: str
    __authentication: dict
    __cloud_devices: dict
    __cloud_device: dict

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.__login_control = LoginControl()
        self.__cloud_devices = {}
        self.__cloud_device = None

    async def async_step_user(self, user_input=None):
        errors = {}

        if self.hass.data.get(DOMAIN) is None:
            self.hass.data[DOMAIN] = {}
        if self.hass.data[DOMAIN].get(DATA_STORE) is None:
            self.hass.data[DOMAIN][DATA_STORE] = {}
        self.__authentication = self.hass.data[DOMAIN][DATA_STORE].get(
            "authentication", None
        )

        if user_input is not None:
            if user_input["setup_mode"] == "cloud":
                try:
                    if self.__authentication is not None:
                        self.__cloud_devices = await self.load_device_info()
                        return await self.async_step_choose_device(None)
                except Exception as e:
                    # Re-authentication is needed.
                    _LOGGER.warning("Connection test failed with %s %s", type(e), e)
                    _LOGGER.warning("Re-authentication is required.")
                return await self.async_step_cloud(None)
            if user_input["setup_mode"] == "manual":
                return await self.async_step_local(None)

        # Build form
        fields: OrderedDict[vol.Marker, Any] = OrderedDict()
        fields[vol.Required("setup_mode")] = SelectSelector(
            SelectSelectorConfig(
                options=["cloud", "manual"],
                mode=SelectSelectorMode.LIST,
                translation_key="setup_mode",
            )
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(fields),
            errors=errors or {},
            last_step=False,
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step user."""
        errors = {}
        placeholders = {}

        if user_input is not None:
            success, response = await self.__async_get_qr_code(
                user_input[CONF_USER_CODE]
            )
            if success:
                return await self.async_step_scan(None)

            errors["base"] = "login_error"
            placeholders = {
                TUYA_RESPONSE_MSG: response.get(TUYA_RESPONSE_MSG, "Unknown error"),
                TUYA_RESPONSE_CODE: response.get(TUYA_RESPONSE_CODE, "0"),
            }
        else:
            user_input = {}

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USER_CODE, default=user_input.get(CONF_USER_CODE, "")
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step scan."""
        if user_input is None:
            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema(
                    {
                        vol.Optional("QR"): QrCodeSelector(
                            config=QrCodeSelectorConfig(
                                data=f"tuyaSmart--qrLogin?token={self.__qr_code}",
                                scale=5,
                                error_correction_level=QrErrorCorrectionLevel.QUARTILE,
                            )
                        )
                    }
                ),
            )

        ret, info = await self.hass.async_add_executor_job(
            self.__login_control.login_result,
            self.__qr_code,
            TUYA_CLIENT_ID,
            self.__user_code,
        )
        if not ret:
            # Try to get a new QR code on failure
            await self.__async_get_qr_code(self.__user_code)
            return self.async_show_form(
                step_id="scan",
                errors={"base": "login_error"},
                data_schema=vol.Schema(
                    {
                        vol.Optional("QR"): QrCodeSelector(
                            config=QrCodeSelectorConfig(
                                data=f"tuyaSmart--qrLogin?token={self.__qr_code}",
                                scale=5,
                                error_correction_level=QrErrorCorrectionLevel.QUARTILE,
                            )
                        )
                    }
                ),
                description_placeholders={
                    TUYA_RESPONSE_MSG: info.get(TUYA_RESPONSE_MSG, "Unknown error"),
                    TUYA_RESPONSE_CODE: info.get(TUYA_RESPONSE_CODE, 0),
                },
            )

        # Now that we have successfully logged in we can query for devices for the account.
        self.__authentication = {
            "user_code": info[CONF_TERMINAL_ID],
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
        self.hass.data[DOMAIN][DATA_STORE]["authentication"] = self.__authentication
        _LOGGER.debug(f"domain_data is {self.hass.data[DOMAIN]}")

        self.__cloud_devices = await self.load_device_info()

        return await self.async_step_choose_device(None)

    async def load_device_info(self) -> dict:
        token_listener = TokenListener(self.hass)
        manager = Manager(
            TUYA_CLIENT_ID,
            self.__authentication["user_code"],
            self.__authentication["terminal_id"],
            self.__authentication["endpoint"],
            self.__authentication["token_info"],
            token_listener,
        )

        listener = DeviceListener(self.hass, manager)
        manager.add_device_listener(listener)

        # Get all devices from Tuya
        await self.hass.async_add_executor_job(manager.update_device_cache)

        # Register known device IDs
        cloud_devices = {}
        domain_data = self.hass.data.get(DOMAIN)
        for device in manager.device_map.values():
            cloud_device = {
                # TODO - Use constants throughout
                "category": device.category,
                "id": device.id,
                "ip": device.ip,  # This will be the WAN IP address so not usable.
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
                "support_local": device.support_local,  # What does this mean?
                CONF_DEVICE_CID: None,
                "version": None,
            }
            _LOGGER.debug(f"Found device: {cloud_device}")

            existing_id = domain_data.get(cloud_device["id"]) if domain_data else None
            existing_uuid = (
                domain_data.get(cloud_device["uuid"]) if domain_data else None
            )
            if existing_id or existing_uuid:
                _LOGGER.debug("Device is already registered.")
                continue

            _LOGGER.debug(f"Adding device: {cloud_device['id']}")
            cloud_devices[cloud_device["id"]] = cloud_device

        return cloud_devices

    async def async_step_choose_device(self, user_input=None):
        errors = {}
        if user_input is not None:
            device_choice = self.__cloud_devices[user_input["device_id"]]

            if device_choice["ip"] != "":
                # This is a directly addable device.
                if user_input["hub_id"] == "None":
                    device_choice["ip"] = ""
                    self.__cloud_device = device_choice
                    return await self.async_step_search(None)
                else:
                    # Show error if user selected a hub.
                    errors["base"] = "does_not_need_hub"
                    # Fall through to reshow the form.
            else:
                # This is an indirectly addressable device. Need to know which hub it is connected to.
                if user_input["hub_id"] != "None":
                    hub_choice = self.__cloud_devices[user_input["hub_id"]]
                    # Populate uuid and local_key from the child device to pass on complete information to the local step.
                    hub_choice["ip"] = ""
                    hub_choice[CONF_DEVICE_CID] = device_choice["uuid"]
                    hub_choice[CONF_LOCAL_KEY] = device_choice[CONF_LOCAL_KEY]
                    self.__cloud_device = hub_choice
                    return await self.async_step_search(None)
                else:
                    # Show error if user did not select a hub.
                    errors["base"] = "needs_hub"
                    # Fall through to reshow the form.

        device_list = []
        for key in self.__cloud_devices.keys():
            device_entry = self.__cloud_devices[key]
            if device_entry[CONF_LOCAL_KEY] != "":
                if device_entry["online"]:
                    device_list.append(
                        SelectOptionDict(
                            value=key,
                            label=f"{device_entry['name']} ({device_entry['product_name']})",
                        )
                    )
                else:
                    device_list.append(
                        SelectOptionDict(
                            value=key,
                            label=f"{device_entry['name']} ({device_entry['product_name']}) OFFLINE",
                        )
                    )

        _LOGGER.debug(f"Device count: {len(device_list)}")
        if len(device_list) == 0:
            return self.async_abort(reason="no_devices")

        device_selector = SelectSelector(
            SelectSelectorConfig(options=device_list, mode=SelectSelectorMode.DROPDOWN)
        )

        hub_list = []
        hub_list.append(SelectOptionDict(value="None", label="None"))
        for key in self.__cloud_devices.keys():
            hub_entry = self.__cloud_devices[key]
            if hub_entry[CONF_LOCAL_KEY] == "":
                hub_list.append(
                    SelectOptionDict(
                        value=key,
                        label=f"{hub_entry['name']} ({hub_entry['product_name']})",
                    )
                )

        _LOGGER.debug(f"Hub count: {len(hub_list) - 1}")

        hub_selector = SelectSelector(
            SelectSelectorConfig(options=hub_list, mode=SelectSelectorMode.DROPDOWN)
        )

        # Build form
        fields: OrderedDict[vol.Marker, Any] = OrderedDict()
        fields[vol.Required("device_id")] = device_selector
        fields[vol.Required("hub_id")] = hub_selector

        return self.async_show_form(
            step_id="choose_device",
            data_schema=vol.Schema(fields),
            errors=errors or {},
            last_step=False,
        )

    async def async_step_search(self, user_input=None):
        if user_input is not None:
            # Current IP is the WAN IP which is of no use. Need to try and discover to the local IP.
            # This scan will take 18s with the default settings. If we cannot find the device we
            # will just leave the IP address blank and hope the user can discover the IP by other
            # means such as router device IP assignments.
            _LOGGER.debug(
                f"Scanning network to get IP address for {self.__cloud_device['id']}."
            )
            self.__cloud_device["ip"] = ""
            try:
                local_device = await self.hass.async_add_executor_job(
                    scan_for_device, self.__cloud_device["id"]
                )
            except OSError:
                local_device = {"ip": None, "version": ""}

            if local_device["ip"] is not None:
                _LOGGER.debug(f"Found: {local_device}")
                self.__cloud_device["ip"] = local_device["ip"]
                self.__cloud_device["version"] = local_device["version"]
            else:
                _LOGGER.warn(f"Could not find device: {self.__cloud_device['id']}")
            return await self.async_step_local(None)

        return self.async_show_form(
            step_id="search", data_schema=vol.Schema({}), errors={}, last_step=False
        )

    async def async_step_local(self, user_input=None):
        errors = {}
        devid_opts = {}
        host_opts = {"default": ""}
        key_opts = {}
        proto_opts = {"default": 3.3}
        polling_opts = {"default": False}
        devcid_opts = {}

        if self.__cloud_device is not None:
            # We already have some or all of the device settings from the cloud flow. Set them into the defaults.
            devid_opts = {"default": self.__cloud_device["id"]}
            host_opts = {"default": self.__cloud_device["ip"]}
            key_opts = {"default": self.__cloud_device[CONF_LOCAL_KEY]}
            if self.__cloud_device["version"] is not None:
                proto_opts = {"default": float(self.__cloud_device["version"])}
            if self.__cloud_device[CONF_DEVICE_CID] is not None:
                devcid_opts = {"default": self.__cloud_device[CONF_DEVICE_CID]}

        if user_input is not None:
            self.device = await async_test_connection(user_input, self.hass)
            if self.device:
                self.data = user_input
                return await self.async_step_select_type()
            else:
                errors["base"] = "connection"
                devid_opts["default"] = user_input[CONF_DEVICE_ID]
                host_opts["default"] = user_input[CONF_HOST]
                key_opts["default"] = user_input[CONF_LOCAL_KEY]
                if CONF_DEVICE_CID in user_input:
                    devcid_opts["default"] = user_input[CONF_DEVICE_CID]
                proto_opts["default"] = user_input[CONF_PROTOCOL_VERSION]
                polling_opts["default"] = user_input[CONF_POLL_ONLY]

        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID, **devid_opts): str,
                    vol.Required(CONF_HOST, **host_opts): str,
                    vol.Required(CONF_LOCAL_KEY, **key_opts): str,
                    vol.Required(
                        CONF_PROTOCOL_VERSION,
                        **proto_opts,
                    ): vol.In(["auto"] + API_PROTOCOL_VERSIONS),
                    vol.Required(CONF_POLL_ONLY, **polling_opts): bool,
                    vol.Optional(CONF_DEVICE_CID, **devcid_opts): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_type(self, user_input=None):
        if user_input is not None:
            self.data[CONF_TYPE] = user_input[CONF_TYPE]
            return await self.async_step_choose_entities()

        types = []
        best_match = 0
        best_matching_type = None

        async for type in self.device.async_possible_types():
            types.append(type.config_type)
            q = type.match_quality(self.device._get_cached_state())
            if q > best_match:
                best_match = q
                best_matching_type = type.config_type

        best_match = int(best_match)
        dps = self.device._get_cached_state()
        _LOGGER.warning(
            "Device matches %s with quality of %d%%. DPS: %s",
            best_matching_type,
            best_match,
            log_json(dps),
        )
        _LOGGER.warning(
            "Report this to https://github.com/make-all/tuya-local/issues/",
        )
        if types:
            return self.async_show_form(
                step_id="select_type",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_TYPE,
                            default=best_matching_type,
                        ): vol.In(types),
                    }
                ),
            )
        else:
            return self.async_abort(reason="not_supported")

    async def async_step_choose_entities(self, user_input=None):
        if user_input is not None:
            title = user_input[CONF_NAME]
            del user_input[CONF_NAME]

            return self.async_create_entry(
                title=title, data={**self.data, **user_input}
            )
        config = get_config(self.data[CONF_TYPE])
        schema = {vol.Required(CONF_NAME, default=config.name): str}

        return self.async_show_form(
            step_id="choose_entities",
            data_schema=vol.Schema(schema),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def __async_get_qr_code(self, user_code: str) -> tuple[bool, dict[str, Any]]:
        """Get the QR code."""
        response = await self.hass.async_add_executor_job(
            self.__login_control.qr_code,
            TUYA_CLIENT_ID,
            TUYA_SCHEMA,
            user_code,
        )
        if success := response.get(TUYA_RESPONSE_SUCCESS, False):
            self.__user_code = user_code
            self.__qr_code = response[TUYA_RESPONSE_RESULT][TUYA_RESPONSE_QR_CODE]
        return success, response


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Manage the options."""
        errors = {}
        config = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            config = {**config, **user_input}
            device = await async_test_connection(config, self.hass)
            if device:
                return self.async_create_entry(title="", data=user_input)
            else:
                errors["base"] = "connection"

        schema = {
            vol.Required(
                CONF_LOCAL_KEY,
                default=config.get(CONF_LOCAL_KEY, ""),
            ): str,
            vol.Required(CONF_HOST, default=config.get(CONF_HOST, "")): str,
            vol.Required(
                CONF_PROTOCOL_VERSION,
                default=config.get(CONF_PROTOCOL_VERSION, "auto"),
            ): vol.In(["auto"] + API_PROTOCOL_VERSIONS),
            vol.Required(
                CONF_POLL_ONLY, default=config.get(CONF_POLL_ONLY, False)
            ): bool,
            vol.Optional(
                CONF_DEVICE_CID,
                default=config.get(CONF_DEVICE_CID, ""),
            ): str,
        }
        cfg = get_config(config[CONF_TYPE])
        if cfg is None:
            return self.async_abort(reason="not_supported")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


async def async_test_connection(config: dict, hass: HomeAssistant):
    domain_data = hass.data.get(DOMAIN)
    existing = domain_data.get(get_device_id(config)) if domain_data else None
    if existing:
        _LOGGER.info("Pausing existing device to test new connection parameters")
        existing["device"].pause()
        await asyncio.sleep(5)

    try:
        subdevice_id = config.get(CONF_DEVICE_CID)
        device = TuyaLocalDevice(
            "Test",
            config[CONF_DEVICE_ID],
            config[CONF_HOST],
            config[CONF_LOCAL_KEY],
            config[CONF_PROTOCOL_VERSION],
            subdevice_id,
            hass,
            True,
        )
        await device.async_refresh()
        retval = device if device.has_returned_state else None
    except Exception as e:
        _LOGGER.warning("Connection test failed with %s %s", type(e), e)
        retval = None

    if existing:
        _LOGGER.info("Restarting device after test")
        existing["device"].resume()

    return retval


def scan_for_device(id):
    return tinytuya.find_device(dev_id=id)


class DeviceListener(SharingDeviceListener):
    """Device Update Listener."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
    ) -> None:
        """Init DeviceListener."""
        self.hass = hass
        self.manager = manager

    def update_device(self, device: CustomerDevice) -> None:
        """Update device status."""
        _LOGGER.debug(
            "Received update for device %s: %s",
            device.id,
            self.manager.device_map[device.id].status,
        )

    def add_device(self, device: CustomerDevice) -> None:
        """Add device added listener."""
        _LOGGER.debug(
            "Received add device %s: %s",
            device.id,
            self.manager.device_map[device.id].status,
        )

    def remove_device(self, device_id: str) -> None:
        """Add device removed listener."""
        _LOGGER.debug(
            "Received remove device %s: %s",
            device_id,
            self.manager.device_map[device_id].status,
        )


class TokenListener(SharingTokenListener):
    """Token listener for upstream token updates."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Init TokenListener."""
        self.hass = hass

    def update_token(self, token_info: dict[str, Any]) -> None:
        """Update token info in config entry."""
        _LOGGER.debug("update_token")
