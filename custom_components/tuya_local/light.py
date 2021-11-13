"""
Setup for different kinds of Tuya light devices
"""
import logging

from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_TYPE,
)
from .generic.light import TuyaLocalLight
from .helpers.device_config import get_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the light device according to its type."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]
    lights = []

    cfg = get_config(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity == "light" and discovery_info.get(ecfg.config_id, False):
        data[ecfg.config_id] = TuyaLocalLight(device, ecfg)
        lights.append(data[ecfg.config_id])
        if ecfg.deprecated:
            _LOGGER.warning(ecfg.deprecation_message)
        _LOGGER.debug(f"Adding light for {device.name}/{ecfg.name}")

    for ecfg in cfg.secondary_entities():
        if ecfg.entity == "light" and discovery_info.get(ecfg.config_id, False):
            data[ecfg.config_id] = TuyaLocalLight(device, ecfg)
            lights.append(data[ecfg.config_id])
            if ecfg.deprecated:
                _LOGGER.warning(ecfg.deprecation_message)
            _LOGGER.debug(f"Adding light for {ecfg.name}")

    if not lights:
        raise ValueError(f"{device.name} does not support use as a light device.")

    async_add_entities(lights)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_setup_platform(hass, {}, async_add_entities, config)
