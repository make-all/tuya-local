"""
Helper for general config
"""

import logging

from .. import DOMAIN
from ..const import CONF_DEVICE_CID, CONF_DEVICE_ID, CONF_TYPE
from .device_config import get_config

_LOGGER = logging.getLogger(__name__)


async def async_tuya_setup_platform(
    hass, async_add_entities, discovery_info, platform, entity_class
):
    """Common functions for async_setup_platform for each entity platform."""
    data = hass.data[DOMAIN][get_device_id(discovery_info)]
    device = data["device"]
    entities = []

    cfg = get_config(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity == platform:
        try:
            data[ecfg.config_id] = entity_class(device, ecfg)
            entities.append(data[ecfg.config_id])
            if ecfg.deprecated:
                _LOGGER.warning(ecfg.deprecation_message)
            _LOGGER.debug("Adding %s for %s", platform, ecfg.config_id)
        except Exception as e:
            _LOGGER.error(
                "Error adding %s for %s: %s",
                ecfg.config_id,
                cfg.config,
                e,
            )

    for ecfg in cfg.secondary_entities():
        if ecfg.entity == platform:
            try:
                data[ecfg.config_id] = entity_class(device, ecfg)
                entities.append(data[ecfg.config_id])
                if ecfg.deprecated:
                    _LOGGER.warning(ecfg.deprecation_message)
                _LOGGER.debug("Adding %s for %s", platform, ecfg.config_id)
            except Exception as e:
                _LOGGER.error(
                    "Error adding %s for %s: %s",
                    ecfg.config_id,
                    cfg.config,
                    e,
                )

    if not entities:
        raise ValueError(f"{device.name} does not support use as a {platform} device.")

    async_add_entities(entities)


def get_device_id(config: dict):
    return (
        config[CONF_DEVICE_CID]
        if CONF_DEVICE_CID in config and config[CONF_DEVICE_CID] != ""
        else config[CONF_DEVICE_ID]
    )
