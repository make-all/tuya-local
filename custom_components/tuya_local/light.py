"""
Setup for different kinds of Tuya light devices
"""
import logging

from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_LIGHT,
    CONF_TYPE,
)
from .generic.light import TuyaLocalLight
from .helpers.device_config import config_for_legacy_use

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the light device according to its type."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]

    cfg = config_for_legacy_use(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity != "light":
        for ecfg in cfg.secondary_entities():
            if ecfg.entity == "light":
                break
        if ecfg.entity != "light":
            raise ValueError(f"{device.name} does not support use as a light device.")
    if ecfg.deprecated:
        _LOGGER.warning(ecfg.deprecation_message)

    data[CONF_LIGHT] = TuyaLocalLight(device, ecfg)
    async_add_entities([data[CONF_LIGHT]])
    _LOGGER.debug(f"Adding light for {discovery_info[CONF_TYPE]}")


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
