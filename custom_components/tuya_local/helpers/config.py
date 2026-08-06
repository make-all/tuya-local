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

    cfg = await hass.async_add_executor_job(
        get_config,
        discovery_info[CONF_TYPE],
    )
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    for ecfg in cfg.all_entities():
        if ecfg.entity == platform:
            try:
                data[ecfg.config_id] = entity_class(device, ecfg)
                entities.append(data[ecfg.config_id])
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
    device_id = config.get(CONF_DEVICE_ID)
    device_cid = config.get(CONF_DEVICE_CID)
    if device_id and device_cid:
        return f"{device_id}/{device_cid}"
    return device_cid or device_id
