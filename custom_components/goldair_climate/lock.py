"""
Setup for different kinds of Goldair climate devices
"""
from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_DEHUMIDIFIER,
    CONF_TYPE_FAN,
    CONF_TYPE_GECO_HEATER,
    CONF_TYPE_GPCV_HEATER,
    CONF_TYPE_GPPH_HEATER,
    CONF_CHILD_LOCK,
    CONF_TYPE_AUTO,
)
from .dehumidifier.lock import GoldairDehumidifierChildLock
from .gpcv_heater.lock import GoldairGPCVHeaterChildLock
from .geco_heater.lock import GoldairGECOHeaterChildLock
from .heater.lock import GoldairHeaterChildLock
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Goldair climate device according to its type."""
    _LOGGER.debug(f"Domain data: {hass.data[DOMAIN]}")
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]

    if discovery_info[CONF_TYPE] == CONF_TYPE_AUTO:
        discovery_info[CONF_TYPE] = await device.async_inferred_type()

        if discovery_info[CONF_TYPE] is None:
            raise ValueError(f"Unable to detect type for device {device.name}")

    if discovery_info[CONF_TYPE] == CONF_TYPE_GPPH_HEATER:
        data[CONF_CHILD_LOCK] = GoldairHeaterChildLock(device)
    elif discovery_info[CONF_TYPE] == CONF_TYPE_DEHUMIDIFIER:
        data[CONF_CHILD_LOCK] = GoldairDehumidifierChildLock(device)
    elif discovery_info[CONF_TYPE] == CONF_TYPE_FAN:
        raise ValueError("Goldair fans do not support child lock.")
    elif discovery_info[CONF_TYPE] == CONF_TYPE_GECO_HEATER:
        data[CONF_CHILD_LOCK] = GoldairGECOHeaterChildLock(device)
    elif discovery_info[CONF_TYPE] == CONF_TYPE_GPCV_HEATER:
        data[CONF_CHILD_LOCK] = GoldairGPCVHeaterChildLock(device)

    if CONF_CHILD_LOCK in data:
        async_add_entities([data[CONF_CHILD_LOCK]])


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
