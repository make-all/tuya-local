"""
Platform to control the child lock on Goldair WiFi-connected dehumidifiers.
"""
try:
    from homeassistant.components.lock import LockEntity
except ImportError:
    from homeassistant.components.lock import LockDevice as LockEntity

from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..device import GoldairTuyaDevice
from .const import ATTR_CHILD_LOCK, PROPERTY_TO_DPS_ID


class GoldairDehumidifierChildLock(LockEntity):
    """Representation of a Goldair WiFi-connected dehumidifier child lock."""

    def __init__(self, device):
        """Initialize the lock.
        Args:
            device (GoldairTuyaDevice): The device API instance."""
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
    def unique_id(self):
        """Return the unique id for this dehumidifier child lock."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this dehumidifier child lock."""
        return self._device.device_info

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

    async def async_lock(self, **kwargs):
        """Turn on the child lock."""
        await self._device.async_set_property(PROPERTY_TO_DPS_ID[ATTR_CHILD_LOCK], True)

    async def async_unlock(self, **kwargs):
        """Turn off the child lock."""
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_CHILD_LOCK], False
        )

    async def async_update(self):
        await self._device.async_refresh()
