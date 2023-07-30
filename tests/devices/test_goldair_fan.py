from homeassistant.components.fan import FanEntityFeature

from ..const import FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
FANMODE_DPS = "2"
PRESET_DPS = "3"
SWING_DPS = "8"
TIMER_DPS = "11"
LIGHT_DPS = "101"


class TestGoldairFan(BasicLightTests, SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("goldair_fan.yaml", FAN_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.mark_secondary(["light_display"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                FanEntityFeature.OSCILLATE
                | FanEntityFeature.PRESET_MODE
                | FanEntityFeature.SET_SPEED
            ),
        )

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

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

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "sleep")

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["normal", "nature", "sleep"])

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_nature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "nature"},
        ):
            await self.subject.async_set_preset_mode("nature")

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertFalse(self.subject.oscillating)

        self.dps[SWING_DPS] = True
        self.assertTrue(self.subject.oscillating)

        self.dps[SWING_DPS] = None
        self.assertFalse(self.subject.oscillating)

    async def test_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: False}
        ):
            await self.subject.async_oscillate(False)

    async def test_oscillate_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: True}
        ):
            await self.subject.async_oscillate(True)

    def test_speed(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[FANMODE_DPS] = 6
        self.assertEqual(self.subject.percentage, 50)

    async def test_set_speed_in_normal_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[SWITCH_DPS] = True
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 3}):
            await self.subject.async_set_percentage(25)

    async def test_set_speed_in_normal_mode_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[SWITCH_DPS] = True
        async with assert_device_properties_set(
            self.subject._device, {FANMODE_DPS: 10}
        ):
            await self.subject.async_set_percentage(80)

    async def test_set_speed_in_sleep_mode_while_off_snaps_and_turns_on(self):
        self.dps[PRESET_DPS] = "sleep"
        self.dps[SWITCH_DPS] = False
        async with assert_device_properties_set(
            self.subject._device, {FANMODE_DPS: 8, SWITCH_DPS: True}
        ):
            await self.subject.async_set_percentage(75)

    async def test_set_speed_to_zero_turns_off(self):
        self.dps[SWITCH_DPS] = True
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_set_percentage(0)

    def test_extra_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.assertEqual(self.subject.extra_state_attributes, {"timer": "5"})

    def test_light_icon(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")
