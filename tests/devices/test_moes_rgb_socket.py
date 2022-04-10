"""Tests for the MoesHouse RGBW smart socket."""
from homeassistant.components.light import (
    COLOR_MODE_RGBW,
    COLOR_MODE_WHITE,
    EFFECT_COLORLOOP,
    SUPPORT_EFFECT,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    ELECTRIC_CURRENT_MILLIAMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    POWER_WATT,
    TIME_MINUTES,
)

from ..const import MOES_RGB_SOCKET_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

LIGHT_DPS = "1"
MODE_DPS = "2"
BRIGHTNESS_DPS = "3"
UNKNOWN4_DPS = "4"
RGBW_DPS = "5"
SCENE_DPS = "6"
SCENE1_DPS = "7"
SCENE2_DPS = "8"
SCENE3_DPS = "9"
SCENE4_DPS = "10"
SWITCH_DPS = "101"
TIMER_DPS = "102"
CURRENT_DPS = "104"
POWER_DPS = "105"
VOLTAGE_DPS = "106"


class TestMoesRGBWSocket(
    BasicNumberTests,
    MultiSensorTests,
    BasicSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("moes_rgb_socket.yaml", MOES_RGB_SOCKET_PAYLOAD)
        self.light = self.entities.get("light_night_light")

        self.setUpBasicSwitch(
            SWITCH_DPS,
            self.entities.get("switch"),
            device_class=SwitchDeviceClass.OUTLET,
            power_dps=POWER_DPS,
            power_scale=10,
        )
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=TIME_MINUTES,
            scale=60,
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_voltage",
                    "dps": VOLTAGE_DPS,
                    "unit": ELECTRIC_POTENTIAL_VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": "measurement",
                    "testdata": (2300, 230.0),
                },
                {
                    "name": "sensor_current",
                    "dps": CURRENT_DPS,
                    "unit": ELECTRIC_CURRENT_MILLIAMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": "measurement",
                },
                {
                    "name": "sensor_power",
                    "dps": POWER_DPS,
                    "unit": POWER_WATT,
                    "device_class": SensorDeviceClass.POWER,
                    "state_class": "measurement",
                    "testdata": (1234, 123.4),
                },
            ]
        )
        self.mark_secondary(
            [
                "number_timer",
                "sensor_current",
                "sensor_power",
                "sensor_voltage",
            ]
        )

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertTrue(self.light.is_on)
        self.dps[LIGHT_DPS] = False
        self.assertFalse(self.light.is_on)

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 45
        self.assertEqual(self.light.brightness, 45)

    def test_light_color_mode(self):
        self.dps[MODE_DPS] = "colour"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[MODE_DPS] = "white"
        self.assertEqual(self.light.color_mode, COLOR_MODE_WHITE)
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[MODE_DPS] = "scene_1"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[MODE_DPS] = "scene_2"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[MODE_DPS] = "scene_3"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)
        self.dps[MODE_DPS] = "scene_4"
        self.assertEqual(self.light.color_mode, COLOR_MODE_RGBW)

    def test_light_rgbw_color(self):
        self.dps[RGBW_DPS] = "ffff00003cffff"
        self.assertSequenceEqual(
            self.light.rgbw_color,
            (255, 255, 0, 255),
        )

    def test_light_effect_list(self):
        self.assertCountEqual(
            self.light.effect_list,
            [
                EFFECT_COLORLOOP,
                "Scene 1",
                "Scene 2",
                "Scene 3",
                "Scene 4",
            ],
        )

    def test_light_effect(self):
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.light.effect, EFFECT_COLORLOOP)
        self.dps[MODE_DPS] = "scene_1"
        self.assertEqual(self.light.effect, "Scene 1")
        self.dps[MODE_DPS] = "scene_2"
        self.assertEqual(self.light.effect, "Scene 2")
        self.dps[MODE_DPS] = "scene_3"
        self.assertEqual(self.light.effect, "Scene 3")
        self.dps[MODE_DPS] = "scene_4"
        self.assertEqual(self.light.effect, "Scene 4")

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            {COLOR_MODE_RGBW, COLOR_MODE_WHITE},
        )

    def test_light_supported_features(self):
        self.assertEqual(self.light.supported_features, SUPPORT_EFFECT)

    async def test_turn_on(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_turn_off()

    async def test_set_brightness(self):
        async with assert_device_properties_set(
            self.light._device,
            {
                LIGHT_DPS: True,
                MODE_DPS: "white",
                BRIGHTNESS_DPS: 128,
            },
        ):
            await self.light.async_turn_on(color_mode=COLOR_MODE_WHITE, brightness=128)

    async def test_set_rgbw(self):
        async with assert_device_properties_set(
            self.light._device,
            {
                LIGHT_DPS: True,
                MODE_DPS: "colour",
                RGBW_DPS: "ff00000000ffff",
            },
        ):
            await self.light.async_turn_on(
                color_mode=COLOR_MODE_RGBW, rgbw_color=(255, 0, 0, 255)
            )

    def test_extra_state_attributes_set(self):
        self.dps[UNKNOWN4_DPS] = 4
        self.dps[SCENE_DPS] = "scene"
        self.dps[SCENE1_DPS] = "scene1"
        self.dps[SCENE2_DPS] = "scene2"
        self.dps[SCENE3_DPS] = "scene3"
        self.dps[SCENE4_DPS] = "scene4"

        self.assertDictEqual(
            self.light.extra_state_attributes,
            {
                "unknown_4": 4,
                "scene_data": "scene",
                "flash_scene_1": "scene1",
                "flash_scene_2": "scene2",
                "flash_scene_3": "scene3",
                "flash_scene_4": "scene4",
            },
        )
