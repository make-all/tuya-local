"""
Setup for different kinds of Tuya lock devices
"""
import logging

from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_LOCK,
    CONF_TYPE,
)
from .generic.lock import TuyaLocalLock
from .helpers.device_config import config_for_legacy_use

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the lock device according to its type."""
    _LOGGER.debug(f"Domain data: {hass.data[DOMAIN]}")
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]

    cfg = config_for_legacy_use(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity != "lock":
        for ecfg in cfg.secondary_entities():
            if ecfg.entity == "lock":
                break
        if ecfg.entity != "lock":
            raise ValueError(f"{device.name} does not support use as a lock device.")
    if ecfg.deprecated:
        _LOGGER.warning(ecfg.deprecation_message)

    data[CONF_LOCK] = TuyaLocalLock(device, ecfg)
    async_add_entities([data[CONF_LOCK]])
    _LOGGER.debug(f"Adding lock for {discovery_info[CONF_TYPE]}")


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
