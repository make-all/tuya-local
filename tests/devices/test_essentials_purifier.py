"""Tests for the essentials air purifier."""

from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfTime,
)

from ..const import ESSENTIALS_PURIFIER_PAYLOAD
from ..mixins.button import BasicButtonTests
from ..mixins.lock import BasicLockTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DP = "1"
PM25_DP = "2"
MODE_DP = "3"
FILTER_DP = "5"
LOCK_DP = "7"
UV_DP = "9"
RESET_DP = "11"
TIMER_DP = "18"
COUNTDOWN_DP = "19"
QUALITY_DP = "21"
LIGHT_DP = "101"


class TestEssentialsPurifier(
    BasicButtonTests,
    BasicLockTests,
    MultiSelectTests,
    MultiSensorTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("essentials_purifier.yaml", ESSENTIALS_PURIFIER_PAYLOAD)
        self.setUpBasicButton(
            RESET_DP,
            self.entities.get("button_filter_reset"),
            ButtonDeviceClass.RESTART,
        )
        self.setUpBasicLock(LOCK_DP, self.entities.get("lock_child_lock"))
        self.setUpMultiSelect(
            [
                {
                    "dps": LIGHT_DP,
                    "name": "select_light",
                    "options": {
                        "Standard": "On",
                        "Soft": "Soft",
                        "Close": "Off",
                    },
                },
                {
                    "dps": TIMER_DP,
                    "name": "select_timer",
                    "options": {
                        "cancel": "Off",
                        "2h": "2 hours",
                        "4h": "4 hours",
                        "8h": "8 hours",
                    },
                },
                {
                    "dps": MODE_DP,
                    "name": "select_mode",
                    "options": {
                        "auto": "Auto",
                        "M": "Medium",
                        "H": "High",
                        "sleep": "Sleep",
                    },
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": FILTER_DP,
                    "name": "sensor_active_filter_life",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": COUNTDOWN_DP,
                    "name": "sensor_time_remaining",
                    "unit": UnitOfTime.MINUTES,
                    "device_class": SensorDeviceClass.DURATION,
                },
                {
                    "dps": PM25_DP,
                    "name": "sensor_pm25",
                    "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                    "device_class": SensorDeviceClass.PM25,
                    "state_class": "measurement",
                },
                {
                    "dps": QUALITY_DP,
                    "name": "sensor_air_quality",
                },
            ]
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": SWITCH_DP,
                    "name": "switch",
                },
                {
                    "dps": UV_DP,
                    "name": "switch_uv_sterilization",
                },
            ]
        )
        self.mark_secondary(
            [
                "button_filter_reset",
                "sensor_active_filter_life",
                "lock_child_lock",
                "select_light",
                "switch_uv_sterilization",
                "select_timer",
                "sensor_time_remaining",
            ]
        )
