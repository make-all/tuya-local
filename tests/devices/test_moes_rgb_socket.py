"""Tests for the MoesHouse RGB smart socket."""

from homeassistant.components.light import (
    EFFECT_OFF,
    ColorMode,
    LightEntityFeature,
)
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTime,
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
RGB_DPS = "5"
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


class TestMoesRGBSocket(
    BasicNumberTests,
    MultiSensorTests,
    BasicSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("moes_rgb_socket.yaml", MOES_RGB_SOCKET_PAYLOAD)
        self.light = self.entities.get("light_nightlight")

        self.setUpBasicSwitch(
            SWITCH_DPS,
            self.entities.get("switch_outlet"),
            device_class=SwitchDeviceClass.OUTLET,
            power_dps=POWER_DPS,
            power_scale=10,
        )
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=UnitOfTime.MINUTES,
            device_class=NumberDeviceClass.DURATION,
            scale=60,
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_voltage",
                    "dps": VOLTAGE_DPS,
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": "measurement",
                    "testdata": (2300, 230.0),
                },
                {
                    "name": "sensor_current",
                    "dps": CURRENT_DPS,
                    "unit": UnitOfElectricCurrent.MILLIAMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": "measurement",
                },
                {
                    "name": "sensor_power",
                    "dps": POWER_DPS,
                    "unit": UnitOfPower.WATT,
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
                "time_timer",
            ]
        )

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertTrue(self.light.is_on)
        self.dps[LIGHT_DPS] = False
        self.assertFalse(self.light.is_on)

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 45
        self.dps[MODE_DPS] = "white"
        self.assertEqual(self.light.brightness, 23)
        self.dps[RGB_DPS] = "808000003cff80"
        self.dps[MODE_DPS] = "colour"
        self.assertEqual(self.light.brightness, 128)

    def test_light_color_mode(self):
        self.dps[MODE_DPS] = "colour"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "white"
        self.assertEqual(self.light.color_mode, ColorMode.WHITE)
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "scene_1"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "scene_2"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "scene_3"
        self.assertEqual(self.light.color_mode, ColorMode.HS)
        self.dps[MODE_DPS] = "scene_4"
        self.assertEqual(self.light.color_mode, ColorMode.HS)

    def test_light_hs_color(self):
        self.dps[RGB_DPS] = "ffff00003cffff"
        self.dps[BRIGHTNESS_DPS] = 255
        self.assertSequenceEqual(
            self.light.hs_color,
            (60, 100),
        )

    def test_light_effect_list(self):
        self.assertCountEqual(
            self.light.effect_list,
            [
                "Scene",
                "Scene 1",
                "Scene 2",
                "Scene 3",
                "Scene 4",
                EFFECT_OFF,
            ],
        )

    def test_light_effect(self):
        self.dps[MODE_DPS] = "scene"
        self.assertEqual(self.light.effect, "Scene")
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
            {ColorMode.HS, ColorMode.WHITE},
        )

    def test_light_supported_features(self):
        self.assertEqual(self.light.supported_features, LightEntityFeature.EFFECT)

    async def test_turn_on(self):
        self.dps[LIGHT_DPS] = False
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_turn_off()

    async def test_set_brightness(self):
        self.dps[LIGHT_DPS] = True
        self.dps[MODE_DPS] = "white"
        async with assert_device_properties_set(
            self.light._device,
            {
                BRIGHTNESS_DPS: 140,
            },
        ):
            await self.light.async_turn_on(brightness=128)

    async def test_set_hs_color(self):
        self.dps[BRIGHTNESS_DPS] = 255
        self.dps[LIGHT_DPS] = True
        self.dps[MODE_DPS] = "colour"

        async with assert_device_properties_set(
            self.light._device,
            {
                RGB_DPS: "ff00000000ffff",
            },
        ):
            await self.light.async_turn_on(hs_color=(0, 100))

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
