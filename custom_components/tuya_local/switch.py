"""
Setup for different kinds of Tuya switch devices
"""
from . import DOMAIN
from .const import (
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_KOGAN_SWITCH,
    CONF_TYPE_PURLINE_M100_HEATER,
    CONF_TYPE_AUTO,
    CONF_SWITCH,
)
from .kogan_socket.switch import KoganSocketSwitch
from .purline_m100_heater.switch import PurlineM100OpenWindowDetector


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch device according to its type."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]

    if discovery_info[CONF_TYPE] == CONF_TYPE_AUTO:
        discovery_info[CONF_TYPE] = await device.async_inferred_type()

        if discovery_info[CONF_TYPE] is None:
            raise ValueError(f"Unable to detect type for device {device.name}")

    if discovery_info[CONF_TYPE] == CONF_TYPE_KOGAN_SWITCH:
        data[CONF_SWITCH] = KoganSocketSwitch(device)
    elif discovery_info[CONF_TYPE] == CONF_TYPE_PURLINE_M100_HEATER:
        data[CONF_SWITCH] = PurlineM100OpenWindowDetector(device)
    else:
        raise ValueError("This device does not support working as a switch")

    if CONF_SWITCH in data:
        async_add_entities([data[CONF_SWITCH]])


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
