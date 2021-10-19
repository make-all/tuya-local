from homeassistant.components.fan import SUPPORT_SET_SPEED
from homeassistant.components.light import COLOR_MODE_ONOFF

from homeassistant.const import STATE_UNAVAILABLE

from ..const import DETA_FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
SPEED_DPS = "3"
LIGHT_DPS = "9"
MASTER_DPS = "101"
TIMER_DPS = "102"
LIGHT_TIMER_DPS = "103"


class TestDetaFan(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("deta_fan.yaml", DETA_FAN_PAYLOAD)
        self.subject = self.entities["fan"]
        self.light = self.entities["light"]
        self.switch = self.entities["switch_master"]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_SET_SPEED,
        )

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

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

    def test_speed(self):
        self.dps[SPEED_DPS] = "1"
        self.assertAlmostEqual(self.subject.percentage, 33.3, 1)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 33.3, 1)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(66.7)

    async def test_auto_stringify_speed(self):
        self.dps[SPEED_DPS] = "1"
        self.assertAlmostEqual(self.subject.percentage, 33.3, 1)
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: "2"}):
            await self.subject.async_set_percentage(66.7)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(55)

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.dps[LIGHT_TIMER_DPS] = "6"
        self.assertEqual(self.subject.device_state_attributes, {"timer": 5})
        self.assertEqual(self.light.device_state_attributes, {"timer": 6})

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, COLOR_MODE_ONOFF)

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertTrue(self.light.is_on)

        self.dps[LIGHT_DPS] = False
        self.assertFalse(self.light.is_on)

    async def test_light_turn_on(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_turn_off()

    def test_switch_is_on(self):
        self.dps[MASTER_DPS] = True
        self.assertTrue(self.switch.is_on)

        self.dps[MASTER_DPS] = False
        self.assertFalse(self.switch.is_on)

        self.dps[MASTER_DPS] = None
        self.assertEqual(self.switch.is_on, STATE_UNAVAILABLE)

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(
            self.switch._device, {MASTER_DPS: True}
        ):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.light._device, {MASTER_DPS: False}
        ):
            await self.switch.async_turn_off()
