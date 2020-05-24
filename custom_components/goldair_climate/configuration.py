import voluptuous as vol
from homeassistant.const import CONF_NAME, CONF_HOST

from .const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_TYPE,
    CONF_TYPE_GPPH_HEATER,
    CONF_TYPE_DEHUMIDIFIER,
    CONF_TYPE_FAN,
    CONF_TYPE_GECO_HEATER,
    CONF_TYPE_GPCV_HEATER,
    CONF_CLIMATE,
    CONF_DISPLAY_LIGHT,
    CONF_CHILD_LOCK,
    CONF_TYPE_AUTO,
)

INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE = [
    {"key": CONF_NAME, "type": str, "required": True, "option": False},
    {"key": CONF_HOST, "type": str, "required": True, "option": True},
    {"key": CONF_DEVICE_ID, "type": str, "required": True, "option": False},
    {"key": CONF_LOCAL_KEY, "type": str, "required": True, "option": True},
    {
        "key": CONF_TYPE,
        "type": vol.In(
            [
                CONF_TYPE_AUTO,
                CONF_TYPE_GPPH_HEATER,
                CONF_TYPE_DEHUMIDIFIER,
                CONF_TYPE_FAN,
                CONF_TYPE_GECO_HEATER,
                CONF_TYPE_GPCV_HEATER,
            ]
        ),
        "required": False,
        "default": CONF_TYPE_AUTO,
        "option": True,
    },
    {
        "key": CONF_CLIMATE,
        "type": bool,
        "required": False,
        "default": True,
        "option": True,
    },
    {
        "key": CONF_DISPLAY_LIGHT,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
    {
        "key": CONF_CHILD_LOCK,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
]


def individual_config_schema(defaults={}, options_only=False):
    output = {}

    for prop in INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE:
        if options_only and not prop.get("option"):
            continue

        options = {}

        default = defaults.get(prop["key"], prop.get("default"))
        if default is not None:
            options["default"] = default

        key = (
            vol.Required(prop["key"], **options)
            if prop["required"]
            else vol.Optional(prop["key"], **options)
        )
        output[key] = prop["type"]

    return output
