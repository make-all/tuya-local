"""
Platform to control the child lock on Goldair WiFi-connected dehumidifiers.
"""
from homeassistant.components.lock import (STATE_LOCKED, STATE_UNLOCKED, LockDevice)
from homeassistant.const import STATE_UNAVAILABLE
from custom_components.tuya_local import TuyaLocalDevice
from custom_components.tuya_local.dehumidifier.climate import (
    ATTR_CHILD_LOCK, PROPERTY_TO_DPS_ID
)


class GoldairDehumidifierChildLock(LockDevice):
    """Representation of a Goldair WiFi-connected dehumidifier child lock."""

    def __init__(self, device):
        """Initialize the lock.
        Args:
            device (TuyaLocalDevice): The device API instance."""
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
        """Return the a boolean representing whether the child lock is on or not."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_CHILD_LOCK])

    def lock(self, **kwargs):
        """Turn on the child lock."""
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_CHILD_LOCK], True)

    def unlock(self, **kwargs):
        """Turn off the child lock."""
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_CHILD_LOCK], False)
