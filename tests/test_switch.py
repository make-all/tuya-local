"""Tests for the switch entity."""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.components.switch import DEVICE_CLASS_OUTLET
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_SWITCH,
    CONF_TYPE,
    CONF_TYPE_AUTO,
    CONF_TYPE_KOGAN_SWITCH,
    DOMAIN,
)
from custom_components.tuya_local.generic.switch import TuyaLocalSwitch
from custom_components.tuya_local.helpers.device_config import config_for_legacy_use
from custom_components.tuya_local.switch import async_setup_entry

from .const import KOGAN_SOCKET_PAYLOAD
from .helpers import assert_device_properties_set

KOGAN_SWITCH_DPS = "1"
KOGAN_TIMER_DPS = "2"
KOGAN_CURRENT_DPS = "4"
KOGAN_POWER_DPS = "5"
KOGAN_VOLTAGE_DPS = "6"


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
    m_device.async_inferred_type = AsyncMock(return_value=CONF_TYPE_KOGAN_SWITCH)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"][CONF_SWITCH]) == TuyaLocalSwitch
    m_add_entities.assert_called_once()


class TestTuyaLocalSwitch(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        kogan_switch_config = config_for_legacy_use(CONF_TYPE_KOGAN_SWITCH)
        switch = kogan_switch_config.primary_entity
        self.switch_name = switch.name
        self.subject = TuyaLocalSwitch(self.mock_device(), switch)
        self.dps = KOGAN_SOCKET_PAYLOAD.copy()

        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.switch_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_is_on(self):
        self.dps[KOGAN_SWITCH_DPS] - True
        self.assertTrue(self.subject.is_on)

        self.dps[KOGAN_SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    def test_is_on_when_unavailable(self):
        self.dps[KOGAN_SWITCH_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {KOGAN_SWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {KOGAN_SWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[KOGAN_SWITCH_DPS] = False

        async with assert_device_properties_set(
            self.subject._device, {KOGAN_SWITCH_DPS: True}
        ):
            await self.subject.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[KOGAN_SWITCH_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {KOGAN_SWITCH_DPS: False}
        ):
            await self.subject.async_toggle()

    def test_current_power_w(self):
        self.dps[KOGAN_POWER_DPS] = 1234
        self.assertEqual(self.subject.current_power_w, 123.4)

    def test_device_state_attributes_set(self):
        self.dps[KOGAN_TIMER_DPS] = 1
        self.dps[KOGAN_VOLTAGE_DPS] = 2350
        self.dps[KOGAN_CURRENT_DPS] = 1234
        self.dps[KOGAN_POWER_DPS] = 5678
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                "timer": 1,
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
            },
        )

        self.dps[KOGAN_TIMER_DPS] = 0
        self.dps[KOGAN_CURRENT_DPS] = None
        self.dps[KOGAN_VOLTAGE_DPS] = None
        self.dps[KOGAN_POWER_DPS] = None
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                "timer": 0,
                "current_a": None,
                "voltage_v": None,
                "current_power_w": None,
            },
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
