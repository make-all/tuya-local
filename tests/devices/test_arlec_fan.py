from homeassistant.components.fan import (
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    FanEntityFeature,
)

from ..const import ARLEC_FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.select import BasicSelectTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
SPEED_DPS = "3"
DIRECTION_DPS = "4"
PRESET_DPS = "102"
TIMER_DPS = "103"


class TestArlecFan(SwitchableTests, BasicSelectTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("arlec_fan.yaml", ARLEC_FAN_PAYLOAD)
        self.subject = self.entities["fan"]
        self.timer = self.entities["select_timer"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities["select_timer"],
            {
                "off": "cancel",
                "2hour": "2h",
                "4hour": "4h",
                "8hour": "8h",
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
                | FanEntityFeature.TURN_OFF
                | FanEntityFeature.TURN_ON
            ),
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "breeze"
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "sleep")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["normal", "nature", "sleep"])

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_breeze(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "breeze"},
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
