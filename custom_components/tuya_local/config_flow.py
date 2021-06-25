import logging

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback

from . import DOMAIN
from .configuration import individual_config_schema
from .device import TuyaLocalDevice
from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_TYPE
from .helpers.device_config import config_for_legacy_use

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            self.device = await async_test_connection(user_input, self.hass)
            if self.device:
                self.data = user_input
                return self.async_step_select_type()
            else:
                errors["base"] = "connection"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(individual_config_schema(user_input or {})),
            errors=errors,
        )

    async def async_step_select_type(self, user_input=None):
        if user_input is not None:
            self.data[CONF_TYPE] = user_input[CONF_TYPE]

        types = []
        async for type in self.device.async_possible_types():
            types.append(type)
        if types:
            return self.async_show_form(
                step_id="type",
                data_schema=vol.Schema({vol.Required(CONF_TYPE): vol.In(types)}),
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
        config = config_for_legacy_use(self.data[CONF_TYPE])
        schema = {vol.Required(CONF_NAME, default=config.name): str}
        e = config.primary_entity
        schema[vol.Optional(e.entity, default=True)] = bool
        for e in config.secondary_entities():
            schema[vol.Optional(e.entity, default=not e.deprecated)] = bool

        return self.async_show_form(
            step_id="entities",
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
            connect_success = await async_test_connection(config, self.hass)
            if connect_success:
                return self.async_create_entry(title="", data=user_input)
            else:
                errors["base"] = "connection"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                individual_config_schema(defaults=config, options_only=True)
            ),
            errors=errors,
        )


async def async_test_connection(config: dict, hass: HomeAssistant):
    device = TuyaLocalDevice(
        "Test", config[CONF_DEVICE_ID], config[CONF_HOST], config[CONF_LOCAL_KEY], hass
    )
    await device.async_refresh()
    return device if device.has_returned_state else None
