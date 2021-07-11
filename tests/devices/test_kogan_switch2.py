"""Tests for the switch entity."""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET
from homeassistant.const import STATE_UNAVAILABLE

from ..const import KOGAN_SOCKET_PAYLOAD2
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "9"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"


class TestKoganSwitch(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("kogan_switch2.yaml", KOGAN_SOCKET_PAYLOAD2)
        self.subject = self.entities.get("switch")

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_is_on(self):
        self.dps[SWITCH_DPS] - True
        self.assertTrue(self.subject.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    def test_is_on_when_unavailable(self):
        self.dps[SWITCH_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[SWITCH_DPS] = False

        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.subject.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[SWITCH_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_toggle()

    def test_current_power_w(self):
        self.dps[POWER_DPS] = 1234
        self.assertEqual(self.subject.current_power_w, 123.4)

    def test_device_state_attributes_set(self):
        self.dps[TIMER_DPS] = 1
        self.dps[VOLTAGE_DPS] = 2350
        self.dps[CURRENT_DPS] = 1234
        self.dps[POWER_DPS] = 5678
        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "timer": 1,
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
            },
        )

        self.dps[TIMER_DPS] = 0
        self.dps[CURRENT_DPS] = None
        self.dps[VOLTAGE_DPS] = None
        self.dps[POWER_DPS] = None
        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "timer": 0,
                "current_a": None,
                "voltage_v": None,
                "current_power_w": None,
            },
        )
