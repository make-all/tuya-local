import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (
    CONF_CLIMATE,
    CONF_DEVICE_ID,
    CONF_FAN,
    CONF_HUMIDIFIER,
    CONF_LIGHT,
    CONF_LOCAL_KEY,
    CONF_LOCK,
    CONF_SWITCH,
    CONF_TYPE,
)
from .helpers.device_config import available_configs, TuyaDeviceConfig


def conf_types():
    types = []
    for cfg in available_configs():
        parsed = TuyaDeviceConfig(cfg)
        types.append(parsed.legacy_type)
    return types


INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE = [
    {"key": CONF_HOST, "type": str, "required": True, "option": True},
    {"key": CONF_DEVICE_ID, "type": str, "required": True, "option": False},
    {"key": CONF_LOCAL_KEY, "type": str, "required": True, "option": True},
]

STAGE2_CONFIG_SCHEMA_TEMPLATE = [
    {"key": CONF_NAME, "type": str, "required": True, "option": False},
    {
        "key": CONF_TYPE,
        "type": vol.In(conf_types()),
        "required": True,
        "option": True,
    },
    {
        "key": CONF_CLIMATE,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
    {
        "key": CONF_LIGHT,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
    {
        "key": CONF_LOCK,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
    {
        "key": CONF_SWITCH,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
    {
        "key": CONF_HUMIDIFIER,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
    {
        "key": CONF_FAN,
        "type": bool,
        "required": False,
        "default": False,
        "option": True,
    },
]


def individual_config_schema(defaults={}, options_only=False, stage=1):
    output = {}
    if options_only:
        schema = [*INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE, *STAGE2_CONFIG_SCHEMA_TEMPLATE]
    elif stage == 1:
        schema = INDIVIDUAL_CONFIG_SCHEMA_TEMPLATE
    else:
        schema = STAGE2_CONFIG_SCHEMA_TEMPLATE

    for prop in schema:
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
