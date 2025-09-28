"""Device scanning utilities for Tuya Local integration."""

import logging

import tinytuya

_LOGGER = logging.getLogger(__name__)


def scan_for_device(device_id: str) -> dict:
    """
    Scan for a Tuya device on the local network.

    Args:
        device_id: The device ID to search for

    Returns:
        Dictionary with device information including IP address
    """
    try:
        return tinytuya.find_device(dev_id=device_id)
    except Exception as e:
        _LOGGER.error("Error scanning for device %s: %s", device_id, e)
        return {"ip": None, "version": ""}
