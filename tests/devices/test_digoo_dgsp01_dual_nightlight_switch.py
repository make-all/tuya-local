"""Tests for the switch entity."""

from homeassistant.components.light import ColorMode, LightEntityFeature
from homeassistant.components.switch import SwitchDeviceClass

from ..const import DIGOO_DGSP01_SOCKET_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
LIGHTSW_DPS = "27"
COLORMODE_DPS = "28"
BRIGHTNESS_DPS = "29"
RGB_DPS = "31"
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
        self.subject = self.entities.get("switch_outlet")
        self.light = self.entities.get("light_nightlight")

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
        self.dps[COLORMODE_DPS] = "white"
        self.assertEqual(self.light.brightness, 23)

    def test_light_color_mode(self):
        self.dps[COLORMODE_DPS] = "colour"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[COLORMODE_DPS] = "white"
        self.assertEqual(self.light.color_mode, ColorMode.WHITE)
        self.dps[COLORMODE_DPS] = "scene"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[COLORMODE_DPS] = "music"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[COLORMODE_DPS] = "scene_1"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[COLORMODE_DPS] = "scene_2"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[COLORMODE_DPS] = "scene_3"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[COLORMODE_DPS] = "scene_4"
        self.assertEqual(self.light.color_mode, ColorMode.HS)

    def test_light_hs_color(self):
        self.dps[RGB_DPS] = "ffff00003c6464"
        self.dps[BRIGHTNESS_DPS] = 255
        self.assertSequenceEqual(self.light.hs_color, (60, 100))

    def test_light_effect_list(self):
        self.assertCountEqual(
            self.light.effect_list,
            [
                "Scene",
                "Music",
                "Scene 1",
                "Scene 2",
                "Scene 3",
                "Scene 4",
            ],
        )

    def test_light_effect(self):
        self.dps[COLORMODE_DPS] = "scene"
        self.assertEqual(self.light.effect, "Scene")
        self.dps[COLORMODE_DPS] = "music"
        self.assertEqual(self.light.effect, "Music")
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
            {ColorMode.HS, ColorMode.WHITE},
        )

    def test_light_supported_features(self):
        self.assertEqual(self.light.supported_features, LightEntityFeature.EFFECT)

    async def test_turn_on(self):
        self.dps[LIGHTSW_DPS] = False
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
        self.dps[COLORMODE_DPS] = "white"
        async with assert_device_properties_set(
            self.light._device,
            {
                BRIGHTNESS_DPS: 140,
            },
        ):
            await self.light.async_turn_on(brightness=128)

    async def test_set_hs_color(self):
        self.dps[RGB_DPS] = "ffffff00000064"
        self.dps[COLORMODE_DPS] = "colour"
        async with assert_device_properties_set(
            self.light._device,
            {
                RGB_DPS: "ff000000006464",
            },
        ):
            await self.light.async_turn_on(hs_color=(0, 100))

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
