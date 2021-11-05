"""
Platform to control Tuya lock devices.

Initial implementation is based on the secondary child-lock feature of Goldair
climate devices.
"""
from homeassistant.components.lock import LockEntity, STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity


class TuyaLocalLock(TuyaLocalEntity, LockEntity):
    """Representation of a Tuya Wi-Fi connected lock."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the lock.
        Args:
          device (TuyaLocalDevice): The device API instance.
          config (TuyaEntityConfig): The configuration for this entity.
        """
        dps_map = self._init_begin(device, config)
        self._lock_dps = dps_map.pop("lock")
        self._init_end(dps_map)

    @property
    def state(self):
        """Return the current state."""
        lock = self._lock_dps.get_value(self._device)

        if lock is None:
            return STATE_UNAVAILABLE
        else:
            return STATE_LOCKED if lock else STATE_UNLOCKED

    @property
    def is_locked(self):
        """Return the a boolean representing whether the lock is locked."""
        return self.state == STATE_LOCKED

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        await self._lock_dps.async_set_value(self._device, True)

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        await self._lock_dps.async_set_value(self._device, False)
