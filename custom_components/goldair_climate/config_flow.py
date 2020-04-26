import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (CONF_NAME, CONF_HOST)
from . import (DOMAIN, individual_config_schema)
from .const import (CONF_DEVICE_ID, CONF_TYPE)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema(individual_config_schema())
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
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        config = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema(individual_config_schema(defaults=config, exclude_fixed=True))
        )
