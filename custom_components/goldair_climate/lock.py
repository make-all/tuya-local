"""
Platform to control the child lock on Goldair WiFi-connected heaters and panels.
"""
from homeassistant.components.lock import (STATE_LOCKED, STATE_UNLOCKED, LockDevice)
from homeassistant.const import STATE_UNAVAILABLE
import custom_components.goldair_climate as goldair_climate


def setup_platform(hass, config, add_devices, discovery_info=None):
    device = hass.data[goldair_climate.DOMAIN][discovery_info['host']]
    add_devices([
        GoldairChildLock(device)
    ])


class GoldairChildLock(LockDevice):
    """Representation of a Goldair WiFi-connected heater child lock."""

    def __init__(self, device):
        """Initialize the lock.
        Args:
            device (GoldairHeaterDevice): The device API instance."""
        self._device = device

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the lock."""
        return self._device.name

    @property
    def state(self):
        """Return the current state."""
        if self.is_locked is None:
            return STATE_UNAVAILABLE
        else:
            return STATE_LOCKED if self.is_locked else STATE_UNLOCKED

    @property
    def is_locked(self):
        """Return the current state."""
        return self._device.is_child_locked

    def lock(self, code):
        """Turn on the LED display."""
        self._device.enable_child_lock()

    def unlock(self, code):
        """Turn off the LED display."""
        self._device.disable_child_lock()
