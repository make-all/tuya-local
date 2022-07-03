from homeassistant.components.light import (
    ColorMode,
    LightEntityFeature,
    EFFECT_COLORLOOP,
    EFFECT_RANDOM,
)
from homeassistant.const import TIME_MINUTES

from ..const import RGBCW_LIGHTBULB_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import BasicNumberTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "20"
MODE_DPS = "21"
BRIGHTNESS_DPS = "22"
COLORTEMP_DPS = "23"
HSV_DPS = "24"
SCENE_DPS = "25"
TIMER_DPS = "26"


class TestRGBCWLightbulb(BasicNumberTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("rgbcw_lightbulb.yaml", RGBCW_LIGHTBULB_PAYLOAD)
        self.subject = self.entities.get("light")

        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=TIME_MINUTES,
            scale=60,
        )
        self.mark_secondary(["number_timer"])

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    def test_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 500
        self.assertAlmostEqual(self.subject.brightness, 128, 0)

    def test_color_temp(self):
        self.dps[COLORTEMP_DPS] = 500
        self.assertAlmostEqual(self.subject.color_temp, 326, 0)
        self.dps[COLORTEMP_DPS] = 1000
        self.assertAlmostEqual(self.subject.color_temp, 153, 0)
        self.dps[COLORTEMP_DPS] = 0
        self.assertAlmostEqual(self.subject.color_temp, 500, 0)

    def test_color_mode(self):
        self.dps[MODE_DPS] = "white"
        self.assertEqual(self.subject.color_mode, ColorMode.COLOR_TEMP)
        self.dps[MODE_DPS] = "colour"
        self.assertEqual(self.subject.color_mode, ColorMode.RGBW)
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.subject.color_mode, ColorMode.RGBW)
        self.dps[MODE_DPS] = "music"
        self.assertEqual(self.subject.color_mode, ColorMode.RGBW)

    def test_rgbw_color(self):
        self.dps[HSV_DPS] = "003c03e803e8"
        self.dps[BRIGHTNESS_DPS] = 1000
        self.assertSequenceEqual(
            self.subject.rgbw_color,
            (255, 255, 0, 255),
        )

    def test_effect_list(self):
        self.assertCountEqual(
            self.subject.effect_list,
            [EFFECT_COLORLOOP, EFFECT_RANDOM],
        )

    def test_effect(self):
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.subject.effect, EFFECT_COLORLOOP)
        self.dps[MODE_DPS] = "music"
        self.assertEqual(self.subject.effect, EFFECT_RANDOM)
        self.dps[MODE_DPS] = "white"
        self.assertIsNone(self.subject.effect)
        self.dps[MODE_DPS] = "colour"
        self.assertIsNone(self.subject.effect)

    def test_supported_color_modes(self):
        self.assertCountEqual(
            self.subject.supported_color_modes,
            {ColorMode.RGBW, ColorMode.COLOR_TEMP},
        )

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, LightEntityFeature.EFFECT)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True},
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: False},
        ):
            await self.subject.async_turn_off()

    async def test_set_brightness(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SWITCH_DPS: True,
                MODE_DPS: "white",
                BRIGHTNESS_DPS: 502,
            },
        ):
            await self.subject.async_turn_on(color_mode=ColorMode.WHITE, brightness=128)

    async def test_set_rgbw(self):
        self.dps[BRIGHTNESS_DPS] = 1000
        async with assert_device_properties_set(
            self.subject._device,
            {
                SWITCH_DPS: True,
                MODE_DPS: "colour",
                HSV_DPS: "000003e803e8",
            },
        ):
            await self.subject.async_turn_on(
                color_mode=ColorMode.RGBW,
                rgbw_color=(255, 0, 0, 255),
            )

    def test_extra_state_attributes(self):
        self.dps[SCENE_DPS] = "test"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "scene_data": "test",
            },
        )
