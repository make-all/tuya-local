from homeassistant.components.light import ColorMode, LightEntityFeature
from homeassistant.const import UnitOfTime

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
            unit=UnitOfTime.MINUTES,
            scale=60,
        )
        self.mark_secondary(["number_timer", "select_scene"])

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    def test_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 500
        self.assertAlmostEqual(self.subject.brightness, 126, 0)

    def test_color_temp(self):
        self.dps[COLORTEMP_DPS] = 500
        self.assertEqual(self.subject.color_temp_kelvin, 4600)
        self.dps[COLORTEMP_DPS] = 1000
        self.assertEqual(self.subject.color_temp_kelvin, 6500)
        self.dps[COLORTEMP_DPS] = 0
        self.assertEqual(self.subject.color_temp_kelvin, 2700)
        self.dps[COLORTEMP_DPS] = None
        self.assertEqual(self.subject.color_temp_kelvin, None)

    def test_color_temp_range(self):
        self.assertEqual(self.subject.min_color_temp_kelvin, 2700)
        self.assertEqual(self.subject.max_color_temp_kelvin, 6500)

    def test_color_mode(self):
        self.dps[MODE_DPS] = "white"
        self.assertEqual(self.subject.color_mode, ColorMode.COLOR_TEMP)
        self.dps[MODE_DPS] = "colour"
        self.assertEqual(self.subject.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.subject.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "music"
        self.assertEqual(self.subject.color_mode, ColorMode.HS)

    def test_hs_color(self):
        self.dps[HSV_DPS] = "003c03e803e8"
        self.dps[BRIGHTNESS_DPS] = 1000
        self.assertSequenceEqual(self.subject.hs_color, (60, 100))

    # Lights have been observed to return N, O and P mixed in with the hex
    # number.  Maybe it has some special meaning, but since it is undocumented,
    # we just want to reject such values without an exception.
    def test_invalid_hs_color(self):
        self.dps[HSV_DPS] = "0010001000OP"
        self.dps[BRIGHTNESS_DPS] = 1000
        self.assertIsNone(self.subject.hs_color)

    def test_effect_list(self):
        self.assertCountEqual(
            self.subject.effect_list,
            ["Scene", "Music"],
        )

    def test_effect(self):
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.subject.effect, "Scene")
        self.dps[MODE_DPS] = "music"
        self.assertEqual(self.subject.effect, "Music")
        self.dps[MODE_DPS] = "white"
        self.assertIsNone(self.subject.effect)
        self.dps[MODE_DPS] = "colour"
        self.assertIsNone(self.subject.effect)

    def test_supported_color_modes(self):
        self.assertCountEqual(
            self.subject.supported_color_modes,
            {ColorMode.HS, ColorMode.COLOR_TEMP},
        )

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, LightEntityFeature.EFFECT)

    async def test_turn_on(self):
        self.dps[SWITCH_DPS] = False
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

    async def test_set_brightness_white(self):
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "white"

        async with assert_device_properties_set(
            self.subject._device,
            {
                BRIGHTNESS_DPS: 506,
            },
        ):
            await self.subject.async_turn_on(brightness=128)

    async def test_set_brightness_color(self):
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "colour"
        self.dps[HSV_DPS] = "000003e803e8"
        async with assert_device_properties_set(
            self.subject._device,
            {
                HSV_DPS: "000003e801f6",
            },
        ):
            await self.subject.async_turn_on(brightness=128)

    async def test_set_hs_color(self):
        self.dps[BRIGHTNESS_DPS] = 1000
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "colour"
        async with assert_device_properties_set(
            self.subject._device,
            {
                HSV_DPS: "000003e803e8",
            },
        ):
            await self.subject.async_turn_on(
                hs_color=(0, 100),
            )

    async def test_set_hs_from_white(self):
        self.dps[BRIGHTNESS_DPS] = 1000
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "white"
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "colour",
                HSV_DPS: "000003e803e8",
            },
        ):
            await self.subject.async_turn_on(
                hs_color=(0, 100),
            )

    def test_extra_state_attributes(self):
        self.dps[SCENE_DPS] = "test"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "scene_data": "test",
            },
        )
