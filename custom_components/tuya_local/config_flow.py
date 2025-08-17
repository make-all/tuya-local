import asyncio
import logging
from collections import OrderedDict
from typing import Any

import tinytuya
import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_PUSH,
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
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

from . import DOMAIN
from .cloud import Cloud
from .const import (
    API_PROTOCOL_VERSIONS,
    CONF_DEVICE_CID,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    CONF_USER_CODE,
    DATA_STORE,
)
from .device import TuyaLocalDevice
from .helpers.config import get_device_id
from .helpers.device_config import get_config
from .helpers.log import log_json

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 13
    MINOR_VERSION = 9
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH
    device = None
    data = {}

    __qr_code: str | None = None
    __cloud_devices: dict[str, Any] = {}
    __cloud_device: dict[str, Any] | None = None

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.cloud = None

    def init_cloud(self):
        if self.cloud is None:
            self.cloud = Cloud(self.hass)

    async def async_step_user(self, user_input=None):
        errors = {}

        if self.hass.data.get(DOMAIN) is None:
            self.hass.data[DOMAIN] = {}
        if self.hass.data[DOMAIN].get(DATA_STORE) is None:
            self.hass.data[DOMAIN][DATA_STORE] = {}

        if user_input is not None:
            mode = user_input.get("setup_mode")
            if mode == "cloud" or mode == "cloud_fresh_login":
                self.init_cloud()
                try:
                    if mode == "cloud_fresh_login":
                        # Force a fresh login
                        self.cloud.logout()

                    if self.cloud.is_authenticated:
                        self.__cloud_devices = await self.cloud.async_get_devices()
                        return await self.async_step_choose_device()
                except Exception as e:
                    # Re-authentication is needed.
                    _LOGGER.warning("Connection test failed with %s %s", type(e), e)
                    _LOGGER.warning("Re-authentication is required.")
                return await self.async_step_cloud()
            if mode == "manual":
                return await self.async_step_local()

        # Build form
        fields: OrderedDict[vol.Marker, Any] = OrderedDict()
        fields[vol.Required("setup_mode")] = SelectSelector(
            SelectSelectorConfig(
                options=["cloud", "manual", "cloud_fresh_login"],
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
        self.init_cloud()

        if user_input is not None:
            response = await self.cloud.async_get_qr_code(user_input[CONF_USER_CODE])
            if response:
                self.__qr_code = response
                return await self.async_step_scan()

            errors["base"] = "login_error"
            placeholders = self.cloud.last_error

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
        self.init_cloud()
        if not await self.cloud.async_login():
            # Try to get a new QR code on failure
            response = await self.cloud.async_get_qr_code()
            errors = {"base": "login_error"}
            placeholders = self.cloud.last_error
            if response:
                self.__qr_code = response

            return self.async_show_form(
                step_id="scan",
                errors=errors,
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
                description_placeholders=placeholders,
            )

        self.__cloud_devices = await self.cloud.async_get_devices()

        return await self.async_step_choose_device()

    async def async_step_choose_device(self, user_input=None):
        errors = {}
        if user_input is not None:
            device_choice = self.__cloud_devices[user_input["device_id"]]

            if device_choice["ip"] != "":
                # This is a directly addable device.
                if user_input["hub_id"] == "None":
                    device_choice["ip"] = ""
                    self.__cloud_device = device_choice
                    return await self.async_step_search()
                else:
                    # Show error if user selected a hub.
                    errors["base"] = "does_not_need_hub"
                    # Fall through to reshow the form.
            else:
                # This is an indirectly addressable device. Need to know which hub it is connected to.
                if user_input["hub_id"] != "None":
                    hub_choice = self.__cloud_devices[user_input["hub_id"]]
                    # Populate node_id or uuid and local_key from the child
                    # device to pass on complete information to the local step.
                    hub_choice["ip"] = ""
                    hub_choice[CONF_DEVICE_CID] = (
                        device_choice["node_id"] or device_choice["uuid"]
                    )
                    if device_choice.get(CONF_LOCAL_KEY):
                        hub_choice[CONF_LOCAL_KEY] = device_choice[CONF_LOCAL_KEY]
                    # Communicate the sub device product id to help match the
                    # correect device config in the next step.
                    hub_choice["product_id"] = device_choice["product_id"]
                    self.__cloud_device = hub_choice
                    return await self.async_step_search()
                else:
                    # Show error if user did not select a hub.
                    errors["base"] = "needs_hub"
                    # Fall through to reshow the form.

        device_list = []
        for key in self.__cloud_devices.keys():
            device_entry = self.__cloud_devices[key]
            if device_entry.get("exists"):
                continue
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
            if hub_entry["is_hub"]:
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
                f"Scanning network to get IP address for {self.__cloud_device.get('id', 'DEVICE_KEY_UNAVAILABLE')}."
            )
            self.__cloud_device["ip"] = ""
            try:
                local_device = await self.hass.async_add_executor_job(
                    scan_for_device, self.__cloud_device.get("id")
                )
            except OSError:
                local_device = {"ip": None, "version": ""}

            if local_device.get("ip"):
                _LOGGER.debug(f"Found: {local_device}")
                self.__cloud_device["ip"] = local_device.get("ip")
                self.__cloud_device["version"] = local_device.get("version")
                if not self.__cloud_device.get(CONF_DEVICE_CID):
                    self.__cloud_device["local_product_id"] = local_device.get(
                        "productKey"
                    )
            else:
                _LOGGER.warning(
                    f"Could not find device: {self.__cloud_device.get('id', 'DEVICE_KEY_UNAVAILABLE')}"
                )
            return await self.async_step_local()

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
            devid_opts = {"default": self.__cloud_device.get("id")}
            host_opts = {"default": self.__cloud_device.get("ip")}
            key_opts = {"default": self.__cloud_device.get(CONF_LOCAL_KEY)}
            if self.__cloud_device.get("version"):
                proto_opts = {"default": float(self.__cloud_device.get("version"))}
            if self.__cloud_device.get(CONF_DEVICE_CID):
                devcid_opts = {"default": self.__cloud_device.get(CONF_DEVICE_CID)}

        if user_input is not None:
            self.device = await async_test_connection(user_input, self.hass)
            if self.device:
                self.data = user_input
                if self.__cloud_device:
                    if self.__cloud_device.get("product_id"):
                        self.device.set_detected_product_id(
                            self.__cloud_device.get("product_id")
                        )
                    if self.__cloud_device.get("local_product_id"):
                        self.device.set_detected_product_id(
                            self.__cloud_device.get("local_product_id")
                        )

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

        for type in await self.device.async_possible_types():
            types.append(type.config_type)
            q = type.match_quality(
                self.device._get_cached_state(),
                self.device._product_ids,
            )
            if q > best_match:
                best_match = q
                best_matching_type = type.config_type

        best_match = int(best_match)
        dps = self.device._get_cached_state()
        if self.__cloud_device:
            _LOGGER.warning(
                "Adding %s device with product id %s",
                self.__cloud_device.get("product_name", "UNKNOWN"),
                self.__cloud_device.get("product_id", "UNKNOWN"),
            )
            if self.__cloud_device.get("local_product_id") and self.__cloud_device.get(
                "local_product_id"
            ) != self.__cloud_device.get("product_id"):
                _LOGGER.warning(
                    "Local product id differs from cloud: %s",
                    self.__cloud_device.get("local_product_id"),
                )
            try:
                self.init_cloud()
                model = await self.cloud.async_get_datamodel(
                    self.__cloud_device.get("id"),
                )
                if model:
                    _LOGGER.warning(
                        "Cloud device spec:\n%s",
                        log_json(model),
                    )
            except Exception as e:
                _LOGGER.warning("Unable to fetch data model from cloud: %s", e)
        _LOGGER.warning(
            "Device matches %s with quality of %d%%. DPS: %s",
            best_matching_type,
            best_match,
            log_json(dps),
        )
        _LOGGER.warning(
            "Include the previous log messages with any new device request to https://github.com/make-all/tuya-local/issues/",
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
        config = await self.hass.async_add_executor_job(
            get_config,
            self.data[CONF_TYPE],
        )
        schema = {vol.Required(CONF_NAME, default=config.name): str}

        return self.async_show_form(
            step_id="choose_entities",
            data_schema=vol.Schema(schema),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlow):
    def __init__(self):
        """Initialize options flow."""
        pass

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
        }
        cfg = await self.hass.async_add_executor_job(
            get_config,
            config[CONF_TYPE],
        )
        if cfg is None:
            return self.async_abort(reason="not_supported")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


def create_test_device(hass: HomeAssistant, config: dict):
    """Set up a tuya device based on passed in config."""
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

    return device


async def async_test_connection(config: dict, hass: HomeAssistant):
    domain_data = hass.data.get(DOMAIN)
    existing = domain_data.get(get_device_id(config)) if domain_data else None
    if existing and existing.get("device"):
        _LOGGER.info("Pausing existing device to test new connection parameters")
        existing["device"].pause()
        await asyncio.sleep(5)

    try:
        device = await hass.async_add_executor_job(
            create_test_device,
            hass,
            config,
        )
        await device.async_refresh()
        retval = device if device.has_returned_state else None
    except Exception as e:
        _LOGGER.warning("Connection test failed with %s %s", type(e), e)
        retval = None

    if existing and existing.get("device"):
        _LOGGER.info("Restarting device after test")
        existing["device"].resume()

    return retval


def scan_for_device(id):
    return tinytuya.find_device(dev_id=id)
