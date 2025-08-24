"""Tests for Mustool MT15/MT29 Airbox, mainly for time entity."""

from ..const import MUSTOOL_MT15MT29_AIRBOX_PAYLOAD
from ..mixins.time import MultiTimeTests
from .base_device_tests import TuyaDeviceTestCase


class TestMustoolMT15MT29Airbox(MultiTimeTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "mustool_mt15mt29_airbox.yaml", MUSTOOL_MT15MT29_AIRBOX_PAYLOAD
        )
        self.setUpMultiTime(
            [
                {
                    "minute": "109",
                    "name": "time_alarm_1",
                    "testdata": {"minute": 600, "time": "10:00:00"},
                },
                {
                    "minute": "110",
                    "name": "time_alarm_2",
                },
                {
                    "minute": "111",
                    "name": "time_alarm_3",
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_battery",
                "binary_sensor_plug",
                "select_alarm_volume",
                "light_backlight",
                "number_co2_alarm_threshold",
                "number_sleep_timer",
                "number_timer",
                "number_alarm_1",
                "number_alarm_2",
                "number_alarm_3",
                "time_alarm_1",
                "time_alarm_2",
                "time_alarm_3",
                "select_temperature_unit",
                "number_co_alarm_threshold",
                "number_pm2_5_alarm_threshold",
                "number_formaldehyde_alarm_threshold",
                "switch_alarm_1",
                "switch_alarm_2",
                "switch_alarm_3",
            ]
        )
