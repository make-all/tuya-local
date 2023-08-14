"""Tests for SD123 Human Presence Radar HPR01"""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from ..const import SD123_PRESENCE_PAYLOAD
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.light import BasicLightTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

PRESENCE_DPS = "1"
SAFERANGE_DPS = "101"
MAXRANGE_DPS = "102"
DELAY_DPS = "103"
MODE_DPS = "104"
UNKNOWN105_DPS = "105"
LIGHT_DPS = "106"
TRIGPOW_DPS = "107"
MAINTPOW_DPS = "108"
TRIGFRAME_DPS = "109"
INTFRAME_DPS = "110"
UNKNOWN111_DPS = "111"
TRIGPOINT_DPS = "112"
MAINTPOINT_DPS = "113"
SWITCH_DPS = "114"


class TestSD123HumanPresenceRadar(
    BasicBinarySensorTests,
    BasicLightTests,
    BasicSwitchTests,
    MultiNumberTests,
    MultiSelectTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("sd123_hpr01_presence.yaml", SD123_PRESENCE_PAYLOAD)
        self.setUpBasicBinarySensor(
            PRESENCE_DPS,
            self.entities.get("binary_sensor_occupancy"),
            device_class=BinarySensorDeviceClass.OCCUPANCY,
            testdata=("presence", "none"),
        )
        self.setUpBasicLight(
            LIGHT_DPS,
            self.entities.get("light_led"),
            testdata=("normal", "slient"),
        )
        self.setUpBasicSwitch(SWITCH_DPS, self.entities.get("switch"))
        self.setUpMultiNumber(
            [
                {
                    "name": "number_trigger_power",
                    "dps": TRIGPOW_DPS,
                    "max": 5000,
                    "step": 100,
                },
                {
                    "name": "number_maintain_power",
                    "dps": MAINTPOW_DPS,
                    "max": 5000,
                    "step": 100,
                },
                {
                    "name": "number_trigger_frames",
                    "dps": TRIGFRAME_DPS,
                    "max": 20,
                },
                {
                    "name": "number_interrupt_frames",
                    "dps": INTFRAME_DPS,
                    "max": 20,
                },
                {
                    "name": "number_trigger_points",
                    "dps": TRIGPOINT_DPS,
                    "max": 10,
                },
                {
                    "name": "number_maintain_points",
                    "dps": MAINTPOINT_DPS,
                    "max": 10,
                },
            ],
        )
        self.setUpMultiSelect(
            [
                {
                    "name": "select_safe_range",
                    "dps": SAFERANGE_DPS,
                    "options": {
                        "0_meters": "0m",
                        "1_meters": "1m",
                        "2_meters": "2m",
                        "3_meters": "3m",
                        "4_meters": "4m",
                        "5_meters": "5m",
                        "6_meters": "6m",
                    },
                },
                {
                    "name": "select_max_range",
                    "dps": MAXRANGE_DPS,
                    "options": {
                        "0_meters": "0m",
                        "1_meters": "1m",
                        "2_meters": "2m",
                        "3_meters": "3m",
                        "4_meters": "4m",
                        "5_meters": "5m",
                        "6_meters": "6m",
                        "7_meters": "7m",
                    },
                },
                {
                    "name": "select_delay",
                    "dps": DELAY_DPS,
                    "options": {
                        "case_0": "10s",
                        "case_1": "30s",
                        "case_2": "1m",
                        "case_3": "2m",
                        "case_4": "5m",
                        "case_5": "10m",
                        "case_6": "30m",
                    },
                },
                {
                    "name": "select_configuration",
                    "dps": MODE_DPS,
                    "options": {
                        "case_0": "Sleep/Micro motion",
                        "case_1": "Meeting/Office",
                        "case_2": "Classroom/Corridor",
                        "case_3": "Custom",
                    },
                },
            ],
        )

        self.mark_secondary(
            [
                "light_led",
                "number_interrupt_frames",
                "number_maintain_points",
                "number_maintain_power",
                "number_trigger_frames",
                "number_trigger_points",
                "number_trigger_power",
                "select_configuration",
                "select_delay",
                "select_max_range",
                "select_safe_range",
                "switch",
            ]
        )

    def test_basic_bsensor_extra_state_attributes(self):
        self.dps[UNKNOWN105_DPS] = "unknown_105"
        self.dps[UNKNOWN111_DPS] = 111

        self.assertDictEqual(
            self.basicBSensor.extra_state_attributes,
            {"unknown_105": "unknown_105", "unknown_111": 111},
        )
