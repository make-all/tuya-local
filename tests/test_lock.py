"""Tests for the lock entity."""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.const import (
    CONF_CHILD_LOCK,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_AUTO,
    CONF_TYPE_GPPH_HEATER,
    DOMAIN,
)
from custom_components.tuya_local.generic.lock import TuyaLocalLock
from custom_components.tuya_local.helpers.device_config import config_for_legacy_use
from custom_components.tuya_local.lock import async_setup_entry

from .const import GPPH_HEATER_PAYLOAD
from .helpers import assert_device_properties_set


GPPH_LOCK_DPS = "6"


async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TYPE: CONF_TYPE_AUTO, CONF_DEVICE_ID: "dummy"},
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()
    m_device.async_inferred_type = AsyncMock(return_value=CONF_TYPE_GPPH_HEATER)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"][CONF_CHILD_LOCK]) == TuyaLocalLock
    m_add_entities.assert_called_once()


class TestTuyaLocalLock(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        gpph_config = config_for_legacy_use(CONF_TYPE_GPPH_HEATER)
        for lock in gpph_config.secondary_entities():
            if lock.entity == "lock":
                break
        self.subject = TuyaLocalLock(self.mock_device(), lock)
        self.dps = GPPH_HEATER_PAYLOAD.copy()
        self.lock_name = lock.name
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.lock_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_state(self):
        self.dps[GPPH_LOCK_DPS] = True
        self.assertEqual(self.subject.state, STATE_LOCKED)

        self.dps[GPPH_LOCK_DPS] = False
        self.assertEqual(self.subject.state, STATE_UNLOCKED)

        self.dps[GPPH_LOCK_DPS] = None
        self.assertEqual(self.subject.state, STATE_UNAVAILABLE)

    def test_state_attributes(self):
        self.assertEqual(self.subject.device_state_attributes, {})

    def test_is_locked(self):
        self.dps[GPPH_LOCK_DPS] = True
        self.assertTrue(self.subject.is_locked)

        self.dps[GPPH_LOCK_DPS] = False
        self.assertFalse(self.subject.is_locked)

    async def test_lock(self):
        async with assert_device_properties_set(
            self.subject._device, {GPPH_LOCK_DPS: True}
        ):
            await self.subject.async_lock()

    async def test_unlock(self):
        async with assert_device_properties_set(
            self.subject._device, {GPPH_LOCK_DPS: False}
        ):
            await self.subject.async_unlock()

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
