"""
Setup for different kinds of Tuya switch devices
"""
import logging

from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_SWITCH,
    CONF_TYPE,
    CONF_TYPE_AUTO,
)
from .helpers.device_config import config_for_legacy_use

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch device according to its type."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]

    if discovery_info[CONF_TYPE] == CONF_TYPE_AUTO:
        discovery_info[CONF_TYPE] = await device.async_inferred_type()

        if discovery_info[CONF_TYPE] is None:
            raise ValueError(f"Unable to detect type for device {device.name}")

    cfg = config_for_legacy_use(discovery_info[CONF_TYPE])
    ecfg = cfg.primary_entity
    if ecfg.entity != "switch":
        for ecfg in cfg.secondary_entities():
            if ecfg.entity == "switch":
                break
        if ecfg.entity != "switch":
            raise ValueError(f"{device.name} does not support use as a switch device.")

    legacy_class = ecfg.legacy_class
    # Instantiate it: Sonarcloud thinks this is a blocker bug, and legacy_class
    # is not callable, but the unit tests show the object is created...
    data[CONF_SWITCH] = legacy_class(device)
    async_add_entities([data[CONF_SWITCH]])
    _LOGGER.debug(f"Adding switch for {discovery_info[CONF_TYPE]}")


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
