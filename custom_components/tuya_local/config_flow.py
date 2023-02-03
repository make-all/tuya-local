import logging

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback

from . import DOMAIN
from .device import TuyaLocalDevice
from .const import (
    API_PROTOCOL_VERSIONS,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
)
from .helpers.device_config import get_config

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 11
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    device = None
    data = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        devid_opts = {}
        host_opts = {"default": "Auto"}
        key_opts = {}
        proto_opts = {"default": "auto"}
        polling_opts = {"default": False}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            self.device = await async_test_connection(user_input, self.hass)
            if self.device:
                self.data = user_input
                return await self.async_step_select_type()
            else:
                errors["base"] = "connection"
                devid_opts["default"] = user_input[CONF_DEVICE_ID]
                host_opts["default"] = user_input[CONF_HOST]
                key_opts["default"] = user_input[CONF_LOCAL_KEY]
                proto_opts["default"] = user_input[CONF_PROTOCOL_VERSION]
                polling_opts["default"] = user_input[CONF_POLL_ONLY]

        return self.async_show_form(
            step_id="user",
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

        if best_match < 100:
            best_match = int(best_match)
            dps = self.device._get_cached_state()
            _LOGGER.warning(
                f"Device matches {best_matching_type} with quality of {best_match}%. DPS: {dps}"
            )
            _LOGGER.warning(
                f"Report this to https://github.com/make-all/tuya-local/issues/"
            )
        if types:
            return self.async_show_form(
                step_id="select_type",
                data_schema=vol.Schema(
                    {vol.Required(CONF_TYPE, default=best_matching_type): vol.In(types)}
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
            vol.Required(CONF_LOCAL_KEY, default=config.get(CONF_LOCAL_KEY, "")): str,
            vol.Required(CONF_HOST, default=config.get(CONF_HOST, "")): str,
            vol.Required(
                CONF_PROTOCOL_VERSION, default=config.get(CONF_PROTOCOL_VERSION, "auto")
            ): vol.In(["auto"] + API_PROTOCOL_VERSIONS),
            vol.Required(
                CONF_POLL_ONLY, default=config.get(CONF_POLL_ONLY, False)
            ): bool,
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
    existing = domain_data.get(config[CONF_DEVICE_ID]) if domain_data else None
    if existing:
        existing["device"].pause()

    device = TuyaLocalDevice(
        "Test",
        config[CONF_DEVICE_ID],
        config[CONF_HOST],
        config[CONF_LOCAL_KEY],
        config[CONF_PROTOCOL_VERSION],
        hass,
        True,
    )
    await device.async_refresh()
    if existing:
        existing["device"].resume()

    return device if device.has_returned_state else None
