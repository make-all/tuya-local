"""Tests for the switch entity."""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET
from homeassistant.const import STATE_UNAVAILABLE

from ..const import GRIDCONNECT_2SOCKET_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
COUNTDOWN1_DPS = "9"
COUNTDOWN2_DPS = "10"
UNKNOWN17_DPS = "17"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"
UNKNOWN21_DPS = "21"
UNKNOWN22_DPS = "22"
UNKNOWN23_DPS = "23"
UNKNOWN24_DPS = "24"
UNKNOWN25_DPS = "25"
UNKNOWN38_DPS = "38"
LOCK_DPS = "40"
MASTER_DPS = "101"


class TestGridConnectDoubleSwitch(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "grid_connect_usb_double_power_point.yaml",
            GRIDCONNECT_2SOCKET_PAYLOAD,
        )
        self.subject = self.entities.get("switch_master")
        self.switch1 = self.entities.get("switch_outlet_1")
        self.switch2 = self.entities.get("switch_outlet_2")
        self.lock = self.entities.get("lock_child_lock")

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_is_on(self):
        self.dps[MASTER_DPS] - True
        self.assertTrue(self.subject.is_on)

        self.dps[MASTER_DPS] = False
        self.assertFalse(self.subject.is_on)

        self.assertEqual(self.switch1.is_on, STATE_UNAVAILABLE)
        self.assertEqual(self.switch1.is_on, STATE_UNAVAILABLE)

        self.dps[MASTER_DPS] = True
        self.dps[SWITCH1_DPS] = True
        self.dps[SWITCH2_DPS] = False
        self.assertTrue(self.switch1.is_on)
        self.assertFalse(self.switch2.is_on)

        self.dps[SWITCH1_DPS] = False
        self.dps[SWITCH2_DPS] = True
        self.assertFalse(self.switch1.is_on)
        self.assertTrue(self.switch2.is_on)

    def test_is_on_when_unavailable(self):
        self.dps[MASTER_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {MASTER_DPS: True}
        ):
            await self.subject.async_turn_on()
        async with assert_device_properties_set(
            self.switch1._device, {SWITCH1_DPS: True}
        ):
            await self.switch1.async_turn_on()
        async with assert_device_properties_set(
            self.switch1._device, {SWITCH2_DPS: True}
        ):
            await self.switch2.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {MASTER_DPS: False}
        ):
            await self.subject.async_turn_off()
        async with assert_device_properties_set(
            self.switch1._device, {SWITCH1_DPS: False}
        ):
            await self.switch1.async_turn_off()
        async with assert_device_properties_set(
            self.switch1._device, {SWITCH2_DPS: False}
        ):
            await self.switch2.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[MASTER_DPS] = False
        self.dps[SWITCH1_DPS] = False
        self.dps[SWITCH2_DPS] = False

        async with assert_device_properties_set(
            self.subject._device, {MASTER_DPS: True}
        ):
            await self.subject.async_toggle()

        self.dps[MASTER_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {SWITCH1_DPS: True}
        ):
            await self.switch1.async_toggle()

        async with assert_device_properties_set(
            self.subject._device, {SWITCH2_DPS: True}
        ):
            await self.switch2.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[MASTER_DPS] = True
        self.dps[SWITCH1_DPS] = True
        self.dps[SWITCH2_DPS] = True
        async with assert_device_properties_set(
            self.subject._device, {SWITCH1_DPS: False}
        ):
            await self.switch1.async_toggle()

        async with assert_device_properties_set(
            self.subject._device, {SWITCH2_DPS: False}
        ):
            await self.switch2.async_toggle()

        async with assert_device_properties_set(
            self.subject._device, {MASTER_DPS: False}
        ):
            await self.subject.async_toggle()

    async def test_turn_on_fails_when_master_is_off(self):
        self.dps[MASTER_DPS] = False
        self.dps[SWITCH1_DPS] = False
        self.dps[SWITCH2_DPS] = False
        with self.assertRaises(AttributeError):
            await self.switch1.async_turn_on()
        with self.assertRaises(AttributeError):
            await self.switch2.async_turn_on()

    def test_current_power_w(self):
        self.dps[POWER_DPS] = 1234
        self.assertEqual(self.subject.current_power_w, 123.4)

    def test_device_state_attributes_set(self):
        self.dps[COUNTDOWN1_DPS] = 9
        self.dps[COUNTDOWN2_DPS] = 10
        self.dps[UNKNOWN17_DPS] = 17
        self.dps[VOLTAGE_DPS] = 2350
        self.dps[CURRENT_DPS] = 1234
        self.dps[POWER_DPS] = 5678
        self.dps[UNKNOWN21_DPS] = 21
        self.dps[UNKNOWN22_DPS] = 22
        self.dps[UNKNOWN23_DPS] = 23
        self.dps[UNKNOWN24_DPS] = 24
        self.dps[UNKNOWN25_DPS] = 25
        self.dps[UNKNOWN38_DPS] = "38"
        self.assertDictEqual(
            self.subject.device_state_attributes,
            {
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
                "unknown_17": 17,
                "unknown_21": 21,
                "unknown_22": 22,
                "unknown_23": 23,
                "unknown_24": 24,
                "unknown_25": 25,
                "unknown_38": "38",
            },
        )
        self.assertDictEqual(
            self.switch1.device_state_attributes,
            {
                "countdown": 9,
            },
        )
        self.assertDictEqual(
            self.switch2.device_state_attributes,
            {
                "countdown": 10,
            },
        )
