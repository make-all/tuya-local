"""
Test MoeBot S mower.
Primarily for testing the STOP command which this device is the first to use,
and the lawn_mower platform.
"""

from homeassistant.components.lawn_mower.const import (
    LawnMowerActivity,
    LawnMowerEntityFeature,
)

from ..const import MOEBOT_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

BATTERY_DP = "6"
STATUS_DP = "101"
ERROR_DP = "102"
PROBLEM_DP = "103"
RAINMODE_DP = "104"
RUNTIME_DP = "105"
PASSWD_DP = "106"
CLEARSCHED_DP = "107"
QUERYSCHED_DP = "108"
QUERYZONE_DP = "109"
SCHEDULE_DP = "110"
ERRLOG_DP = "111"
WORKLOG_DP = "112"
ZONES_DP = "113"
AUTOMODE_DP = "114"
COMMAND_DP = "115"


class TestMoebot(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("moebot_s_mower.yaml", MOEBOT_PAYLOAD)
        self.mower = self.entities.get("lawn_mower")
        self.start_button = self.entities.get("button_start_fixed_mowing")
        self.mark_secondary(
            [
                "binary_sensor_cover",
                "binary_sensor_problem",
                "select_mowing_mode",
                "sensor_problem",
                "switch_rain_mode",
                "number_running_time",
                "button_clear_schedule",
                "button_query_schedule",
                "button_query_zones",
                "switch_hedgehog_protection",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.mower.supported_features,
            (
                LawnMowerEntityFeature.START_MOWING
                | LawnMowerEntityFeature.PAUSE
                | LawnMowerEntityFeature.DOCK
            ),
        )

    def test_lawnmower_activity(self):
        self.dps[STATUS_DP] = "ERROR"
        self.assertEqual(self.mower.activity, LawnMowerActivity.ERROR)
        self.dps[STATUS_DP] = "EMERGENCY"
        self.assertEqual(self.mower.activity, LawnMowerActivity.ERROR)
        self.dps[STATUS_DP] = "PAUSED"
        self.assertEqual(self.mower.activity, LawnMowerActivity.PAUSED)
        self.dps[STATUS_DP] = "PARK"
        self.assertEqual(self.mower.activity, LawnMowerActivity.RETURNING)
        self.dps[STATUS_DP] = "MOWING"
        self.assertEqual(self.mower.activity, LawnMowerActivity.MOWING)
        self.dps[STATUS_DP] = "FIXED_MOWING"
        self.assertEqual(self.mower.activity, LawnMowerActivity.MOWING)
        self.dps[STATUS_DP] = "STANDBY"
        self.assertEqual(self.mower.activity, LawnMowerActivity.DOCKED)
        self.dps[STATUS_DP] = "CHARGING"
        self.assertEqual(self.mower.activity, LawnMowerActivity.DOCKED)
        self.dps[STATUS_DP] = "LOCKED"
        self.assertEqual(self.mower.activity, LawnMowerActivity.DOCKED)
        self.dps[STATUS_DP] = "CHARGING_WITH_TASK_SUSPEND"
        self.assertEqual(self.mower.activity, LawnMowerActivity.DOCKED)

    async def test_async_start_mowing(self):
        async with assert_device_properties_set(
            self.mower._device,
            {COMMAND_DP: "StartMowing"},
        ):
            await self.mower.async_start_mowing()

    async def test_async_start_fixed_mowing(self):
        async with assert_device_properties_set(
            self.start_button._device,
            {COMMAND_DP: "StartFixedMowing"},
        ):
            await self.start_button.async_press()

    async def test_async_pause(self):
        async with assert_device_properties_set(
            self.mower._device,
            {COMMAND_DP: "PauseWork"},
        ):
            await self.mower.async_pause()

    async def test_async_dock(self):
        async with assert_device_properties_set(
            self.mower._device,
            {COMMAND_DP: "StartReturnStation"},
        ):
            await self.mower.async_dock()
