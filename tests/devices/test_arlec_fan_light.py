from homeassistant.components.fan import (
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    FanEntityFeature,
)
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ColorMode

from ..const import ARLEC_FAN_LIGHT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.select import BasicSelectTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
SPEED_DPS = "3"
DIRECTION_DPS = "4"
LIGHT_DPS = "9"
BRIGHTNESS_DPS = "10"
COLORTEMP_DPS = "11"
PRESET_DPS = "102"
TIMER_DPS = "103"


class TestArlecFan(SwitchableTests, BasicSelectTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("arlec_fan_light.yaml", ARLEC_FAN_LIGHT_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.light = self.entities.get("light")
        self.timer = self.entities.get("select_timer")

        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities["select_timer"],
            {
                "off": "Off",
                "2hour": "2 hours",
                "4hour": "4 hours",
                "8hour": "8 hours",
            },
        )
        self.mark_secondary(["select_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                FanEntityFeature.DIRECTION
                | FanEntityFeature.PRESET_MODE
                | FanEntityFeature.SET_SPEED
            ),
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "sleep")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["nature", "sleep"])

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

    def test_direction(self):
        self.dps[DIRECTION_DPS] = "forward"
        self.assertEqual(self.subject.current_direction, DIRECTION_FORWARD)
        self.dps[DIRECTION_DPS] = "reverse"
        self.assertEqual(self.subject.current_direction, DIRECTION_REVERSE)

    async def test_set_direction_forward(self):
        async with assert_device_properties_set(
            self.subject._device, {DIRECTION_DPS: "forward"}
        ):
            await self.subject.async_set_direction(DIRECTION_FORWARD)

    async def test_set_direction_reverse(self):
        async with assert_device_properties_set(
            self.subject._device, {DIRECTION_DPS: "reverse"}
        ):
            await self.subject.async_set_direction(DIRECTION_REVERSE)

    def test_speed(self):
        self.dps[SPEED_DPS] = "3"
        self.assertEqual(self.subject.percentage, 50)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 16.67, 2)
        self.assertEqual(self.subject.speed_count, 6)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(33)

    async def test_set_speed_in_normal_mode_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 5}):
            await self.subject.async_set_percentage(80)

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = False
        self.assertFalse(self.light.is_on)
        self.dps[LIGHT_DPS] = True
        self.assertTrue(self.light.is_on)

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [ColorMode.COLOR_TEMP],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, ColorMode.COLOR_TEMP)

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 50
        self.assertAlmostEqual(self.light.brightness, 128, 0)

    def test_light_color_temp(self):
        self.dps[COLORTEMP_DPS] = 70
        self.assertEqual(self.light.color_temp_kelvin, 3840)

    def test_light_color_temp_range(self):
        self.assertEqual(self.light.min_color_temp_kelvin, 2700)
        self.assertEqual(self.light.max_color_temp_kelvin, 6500)

    async def test_light_async_turn_on(self):
        async with assert_device_properties_set(
            self.light._device,
            {LIGHT_DPS: True, BRIGHTNESS_DPS: 44, COLORTEMP_DPS: 70},
        ):
            await self.light.async_turn_on(
                brightness=112,
                color_temp_kelvin=3840,
            )
