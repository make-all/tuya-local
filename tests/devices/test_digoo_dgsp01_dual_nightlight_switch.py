"""Tests for the switch entity."""
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.light import (
    COLOR_MODE_RGBW,
    COLOR_MODE_WHITE,
    EFFECT_COLORLOOP,
    EFFECT_RANDOM,
    SUPPORT_EFFECT,
)
from ..const import DIGOO_DGSP01_SOCKET_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
LIGHTSW_DPS = "27"
COLORMODE_DPS = "28"
BRIGHTNESS_DPS = "29"
RGBW_DPS = "31"
UNKNOWN32_DPS = "32"
UNKNOWN33_DPS = "33"
UNKNOWN34_DPS = "34"
UNKNOWN35_DPS = "35"
UNKNOWN36_DPS = "36"


class TestDigooNightlightSwitch(BasicSwitchTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "digoo_dgsp01_dual_nightlight_switch.yaml",
            DIGOO_DGSP01_SOCKET_PAYLOAD,
        )
        self.subject = self.entities.get("switch")
        self.light = self.entities.get("light_night_light")

        self.setUpBasicSwitch(
            SWITCH_DPS, self.subject, device_class=SwitchDeviceClass.OUTLET
        )

    def test_light_is_on(self):
        self.dps[LIGHTSW_DPS] = True
        self.assertTrue(self.light.is_on)
        self.dps[LIGHTSW_DPS] = False
        self.assertFalse(self.light.is_on)

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 45
        self.assertEqual(self.light.brightness, 45)

    def test_light_color_mode(self):
        self.dps[COLORMODE_DPS] = "colour"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[COLORMODE_DPS] = "white"
        self.assertEqual(self.light.color_mode, COLOR_MODE_WHITE)
        self.dps[COLORMODE_DPS] = "scene"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[COLORMODE_DPS] = "music"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[COLORMODE_DPS] = "scene_1"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[COLORMODE_DPS] = "scene_2"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[COLORMODE_DPS] = "scene_3"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[COLORMODE_DPS] = "scene_4"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)

    def test_light_rgbw_color(self):
        self.dps[RGBW_DPS] = "ffff00003c6464"
        self.assertSequenceEqual(
            self.light.rgbw_color,
            (255, 255, 0, 255),
        )

    def test_light_effect_list(self):
        self.assertCountEqual(
            self.light.effect_list,
            [
                EFFECT_COLORLOOP,
                EFFECT_RANDOM,
                "Scene 1",
                "Scene 2",
                "Scene 3",
                "Scene 4",
            ],
        )

    def test_light_effect(self):
        self.dps[COLORMODE_DPS] = "scene"
        self.assertEqual(self.light.effect, EFFECT_COLORLOOP)
        self.dps[COLORMODE_DPS] = "music"
        self.assertEqual(self.light.effect, EFFECT_RANDOM)
        self.dps[COLORMODE_DPS] = "scene_1"
        self.assertEqual(self.light.effect, "Scene 1")
        self.dps[COLORMODE_DPS] = "scene_2"
        self.assertEqual(self.light.effect, "Scene 2")
        self.dps[COLORMODE_DPS] = "scene_3"
        self.assertEqual(self.light.effect, "Scene 3")
        self.dps[COLORMODE_DPS] = "scene_4"
        self.assertEqual(self.light.effect, "Scene 4")
        self.dps[COLORMODE_DPS] = "white"
        self.assertIsNone(self.light.effect)
        self.dps[COLORMODE_DPS] = "colour"
        self.assertIsNone(self.light.effect)

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            {COLOR_MODE_RGBW, COLOR_MODE_WHITE},
        )

    def test_light_supported_features(self):
        self.assertEqual(self.light.supported_features, SUPPORT_EFFECT)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.light._device, {LIGHTSW_DPS: True}
        ):
            await self.light.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.light._device, {LIGHTSW_DPS: False}
        ):
            await self.light.async_turn_off()

    async def test_set_brightness(self):
        async with assert_device_properties_set(
            self.light._device,
            {
                LIGHTSW_DPS: True,
                COLORMODE_DPS: "white",
                BRIGHTNESS_DPS: 128,
            },
        ):
            await self.light.async_turn_on(color_mode=COLOR_MODE_WHITE, brightness=128)

    async def test_set_rgbw(self):
        async with assert_device_properties_set(
            self.light._device,
            {
                LIGHTSW_DPS: True,
                COLORMODE_DPS: "colour",
                RGBW_DPS: "ff000000006464",
            },
        ):
            await self.light.async_turn_on(
                color_mode=COLOR_MODE_RGBW, rgbw_color=(255, 0, 0, 255)
            )

    def test_extra_state_attributes_set(self):
        self.dps[UNKNOWN32_DPS] = "32"
        self.dps[UNKNOWN33_DPS] = "33"
        self.dps[UNKNOWN34_DPS] = "34"
        self.dps[UNKNOWN35_DPS] = "35"
        self.dps[UNKNOWN36_DPS] = "36"
        self.assertDictEqual(
            self.light.extra_state_attributes,
            {
                "unknown_32": "32",
                "unknown_33": "33",
                "unknown_34": "34",
                "unknown_35": "35",
                "unknown_36": "36",
            },
        )
