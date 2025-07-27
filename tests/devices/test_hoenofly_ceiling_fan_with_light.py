from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.light import ColorMode

from ..const import CEILING_FAN_WITH_LIGHT_NEW_PAYLOAD
from ..mixins import BasicFanTests, BasicLightTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "105"
SPEED_DPS = "104"
PRESET_DPS = "102"
DIRECTION_DPS = "101"
LIGHT_DPS = "20"
BRIGHTNESS_DPS = "22"
COLORTEMP_DPS = "23"
COLORMODE_DPS = "21"


class TestHoenoflyFanWithLight(
    BasicFanTests, BasicLightTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("hoenofly_ceiling_fan_with_light.yaml", CEILING_FAN_WITH_LIGHT_NEW_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.light = self.entities.get("light")
        self.mark_secondary(["light"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                FanEntityFeature.SET_SPEED
                | FanEntityFeature.DIRECTION
                | FanEntityFeature.PRESET_MODE
            ),
        )

    def test_speed(self):
        self.dps[SPEED_DPS] = 3
        self.assertEqual(self.subject.percentage, 50)

    def test_speed_step(self):
        self.assertEqual(self.subject.speed_count, 6)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["1", "2", "3", "4", "5", "6"],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "level_3"
        self.assertEqual(self.subject.preset_mode, "3")

    def test_direction(self):
        self.dps[DIRECTION_DPS] = "forward"
        self.assertEqual(self.subject.current_direction, "forward")

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 500
        self.assertEqual(self.light.brightness, 128)

    def test_light_color_temp(self):
        self.dps[COLORTEMP_DPS] = 500
        self.assertEqual(self.light.color_temp_kelvin, 4600)

    def test_light_color_mode(self):
        self.dps[COLORMODE_DPS] = "white"
        self.assertEqual(self.light.color_mode, ColorMode.COLOR_TEMP)