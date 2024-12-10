from homeassistant.components.fan import (
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    FanEntityFeature,
)

from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.select import BasicSelectTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

IMAX_NEO_LIGHT_VENTO_PAYLOAD = {
    "1": True,
    "2": "normal",
    "3": "1",
    "8": "forward",
    "15": False,
    "22": "off",
}

SWITCH_DPS = "1"
PRESET_DPS = "2"
SPEED_DPS = "3"
DIRECTION_DPS = "8"
LIGHT_DPS = "15"
TIMER_DPS = "22"


class TestImmaxNeoLightVento(
    SwitchableTests, BasicSelectTests, BasicLightTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("immax_neo_light_vento.yaml", IMAX_NEO_LIGHT_VENTO_PAYLOAD)
        self.fan = self.entities["fan"]
        self.light = self.entities["light"]
        self.stop_timer = self.entities["select_timer"]
        self.setUpSwitchable(SWITCH_DPS, self.fan)
        self.setUpBasicLight(LIGHT_DPS, self.light)
        self.setUpBasicSelect(
            TIMER_DPS,
            self.stop_timer,
            {
                "off": "cancel",
                "1hour": "1h",
                "2hour": "2h",
                "4hour": "4h",
                "8hour": "8h",
            },
        )
        self.mark_secondary(["select_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.fan.supported_features,
            FanEntityFeature.DIRECTION
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON,
        )

    def test_preset_modes(self):
        self.assertCountEqual(self.fan.preset_modes, ["normal", "nature", "sleep"])

    def test_speed(self):
        self.dps[SPEED_DPS] = 2
        self.assertAlmostEqual(33, self.fan.percentage, 0)
        self.dps[SPEED_DPS] = 3
        self.assertEqual(50, self.fan.percentage)
        self.dps[SPEED_DPS] = 4
        self.assertAlmostEqual(66, self.fan.percentage, 0)
        self.dps[SPEED_DPS] = 5
        self.assertAlmostEqual(83, self.fan.percentage, 0)
        self.dps[SPEED_DPS] = 6
        self.assertEqual(100, self.fan.percentage)
        self.dps[SPEED_DPS] = 0
        self.assertEqual(0, self.fan.percentage)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.fan.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.fan.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.fan.preset_mode, "sleep")

    def test_direction(self):
        self.dps[DIRECTION_DPS] = "forward"
        self.assertEqual(self.fan.current_direction, DIRECTION_FORWARD)
        self.dps[DIRECTION_DPS] = "reverse"
        self.assertEqual(self.fan.current_direction, DIRECTION_REVERSE)

    async def test_set_direction_forward(self):
        async with assert_device_properties_set(
            self.fan._device, {DIRECTION_DPS: "forward"}
        ):
            await self.fan.async_set_direction(DIRECTION_FORWARD)

    async def test_set_direction_reverse(self):
        async with assert_device_properties_set(
            self.fan._device, {DIRECTION_DPS: "reverse"}
        ):
            await self.fan.async_set_direction(DIRECTION_REVERSE)

    def test_set_stop_timer(self):
        self.dps[TIMER_DPS] = "2hour"
        self.assertEqual(self.stop_timer.current_option, "2h")

    async def test_set_speed(self):
        async with assert_device_properties_set(self.fan._device, {SPEED_DPS: 2}):
            await self.fan.async_set_percentage(33)

    async def test_set_speed_in_normal_mode_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.fan._device, {SPEED_DPS: 5}):
            await self.fan.async_set_percentage(80)
