"""
Test MoeBot S mower.
Primarily for testing the STOP command which this device is the first to use.
"""
from homeassistant.components.vacuum import VacuumEntityFeature

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
        self.subject = self.entities.get("vacuum")
        self.mark_secondary(
            [
                "binary_sensor_error",
                "sensor_problem",
                "switch_rain_mode",
                "number_running_time",
                "button_clear_schedule",
                "button_query_schedule",
                "button_query_zones",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                VacuumEntityFeature.CLEAN_SPOT
                | VacuumEntityFeature.PAUSE
                | VacuumEntityFeature.RETURN_HOME
                | VacuumEntityFeature.SEND_COMMAND
                | VacuumEntityFeature.START
                | VacuumEntityFeature.STATE
                | VacuumEntityFeature.STATUS
                | VacuumEntityFeature.STOP
            ),
        )

    async def test_async_stop(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "CancelWork"},
        ):
            await self.subject.async_stop()
