# Mixins for testing locks

from ..helpers import assert_device_properties_set


class BasicLockTests:
    def setUpBasicLock(self, dps, subject):
        self.basicLock = subject
        self.basicLockDps = dps

    def test_basic_lock_is_locked(self):
        self.dps[self.basicLockDps] = True
        self.assertTrue(self.basicLock.is_locked)

        self.dps[self.basicLockDps] = False
        self.assertFalse(self.basicLock.is_locked)

        self.dps[self.basicLockDps] = None
        self.assertFalse(self.basicLock.is_locked)

    async def test_basic_lock_locks(self):
        async with assert_device_properties_set(
            self.basicLock._device,
            {self.basicLockDps: True},
        ):
            await self.basicLock.async_lock()

    async def test_basic_lock_unlocks(self):
        async with assert_device_properties_set(
            self.basicLock._device,
            {self.basicLockDps: False},
        ):
            await self.basicLock.async_unlock()

    def test_basic_lock_state_attributes(self):
        self.assertEqual(self.basicLock.extra_state_attributes, {})
