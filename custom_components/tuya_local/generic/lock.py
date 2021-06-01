"""
Platform to control Tuya lock devices.

Initial implementation is based on the secondary child-lock feature of Goldair
climate devices.
"""
from homeassistant.components.lock import LockEntity, STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig


class TuyaLocalLock(LockEntity):
    """Representation of a Tuya Wi-Fi connected lock."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the lock.
        Args:
          device (TuyaLocalDevice): The device API instance.
          config (TuyaEntityConfig): The configuration for this entity.
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        for d in config.dps():
            if d.name == "lock":
                self._lock_dps = d
            elif not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        """Return the name for this entity."""
        return self._device.name

    @property
    def friendly_name(self):
        """Return the friendly name for this entity."""
        return self._config.name

    @property
    def unique_id(self):
        """Return the device unique ID."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return the device information."""
        return self._device.device_info

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

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        await self._lock_dps.async_set_value(self._device, True)

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        await self._lock_dps.async_set_value(self._device, False)

    async def async_update(self):
        await self._device.async_refresh()
