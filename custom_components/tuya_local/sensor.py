"""
Setup for different kinds of Tuya sensors
"""
import logging

from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_TYPE,
)
from .generic.sensor import TuyaLocalSensor
from .helpers.device_config import get_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor device according to it's type."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]
    sensors = []

    cfg = get_config(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity == "sensor" and discovery_info.get(ecfg.config_id, False):
        data[ecfg.config_id] = TuyaLocalSensor(device, ecfg)
        sensors.append(data[ecfg.config_id])
        if ecfg.deprecated:
            _LOGGER.warning(ecfg.deprecation_message)
        _LOGGER.debug(f"Adding sensor for {discovery_info[ecfg.config_id]}")

    for ecfg in cfg.secondary_entities():
        if ecfg.entity == "sensor" and discovery_info.get(ecfg.config_id, False):
            data[ecfg.config_id] = TuyaLocalSensor(device, ecfg)
            sensors.append(data[ecfg.config_id])
            if ecfg.deprecated:
                _LOGGER.warning(ecfg.deprecation_message)
            _LOGGER.debug(f"Adding sensor for {discovery_info[ecfg.config_id]}")

    if not sensors:
        raise ValueError(f"{device.name} does not support use as a sensor device.")
    async_add_entities(sensors)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_setup_platform(hass, {}, async_add_entities, config)
