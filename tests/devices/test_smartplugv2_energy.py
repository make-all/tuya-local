"""Tests for the switch entity."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    ELECTRIC_CURRENT_MILLIAMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_WATT_HOUR,
    POWER_WATT,
    TIME_MINUTES,
)

from ..const import SMARTSWITCH_ENERGY_PAYLOAD
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.number import BasicNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "9"
ENERGY_DPS = "17"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"
TEST_DPS = "21"
CALIBV_DPS = "22"
CALIBI_DPS = "23"
CALIBP_DPS = "24"
CALIBE_DPS = "25"
ERROR_DPS = "26"
INITIAL_DPS = "38"
CYCLE_DPS = "41"
RANDOM_DPS = "42"
OVERCHARGE_DPS = "46"


class TestSwitchV2Energy(
    BasicBinarySensorTests,
    BasicNumberTests,
    BasicSelectTests,
    MultiSensorTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("smartplugv2_energy.yaml", SMARTSWITCH_ENERGY_PAYLOAD)
        self.setUpMultiSwitch(
            [
                {
                    "name": "switch",
                    "dps": SWITCH_DPS,
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "name": "switch_overcharge_cutoff",
                    "dps": OVERCHARGE_DPS,
                },
            ]
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=TIME_MINUTES,
            scale=60,
        )
        self.setUpBasicSelect(
            INITIAL_DPS,
            self.entities.get("select_initial_state"),
            {
                "on": "On",
                "off": "Off",
                "memory": "Last State",
            },
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_energy",
                    "dps": ENERGY_DPS,
                    "unit": ENERGY_WATT_HOUR,
                    "device_class": SensorDeviceClass.ENERGY,
                    "state_class": "total_increasing",
                },
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
                "binary_sensor_error",
                "number_timer",
                "select_initial_state",
                "sensor_current",
                "sensor_energy",
                "sensor_power",
                "sensor_voltage",
                "switch_overcharge_cutoff",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[TEST_DPS] = 21
        self.dps[CALIBV_DPS] = 22
        self.dps[CALIBI_DPS] = 23
        self.dps[CALIBP_DPS] = 24
        self.dps[CALIBE_DPS] = 25
        self.dps[ERROR_DPS] = 26
        self.dps[CYCLE_DPS] = "1A2B"
        self.dps[RANDOM_DPS] = "3C4D"

        self.assertDictEqual(
            self.multiSwitch["switch"].extra_state_attributes,
            {
                "test_bit": 21,
                "voltage_calibration": 22,
                "current_calibration": 23,
                "power_calibration": 24,
                "energy_calibration": 25,
                "fault_code": 26,
                "cycle_timer": "1A2B",
                "random_timer": "3C4D",
            },
        )
