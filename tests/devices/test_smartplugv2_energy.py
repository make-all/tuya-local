"""Tests for the switch entity."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
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
LIGHT_DPS = "39"
LOCK_DPS = "40"
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
                    "name": "switch_outlet",
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
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=UnitOfTime.MINUTES,
            scale=60,
        )
        self.setUpBasicSelect(
            INITIAL_DPS,
            self.entities.get("select_initial_state"),
            {
                "on": "on",
                "off": "off",
                "memory": "memory",
            },
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_energy",
                    "dps": ENERGY_DPS,
                    "unit": UnitOfEnergy.WATT_HOUR,
                },
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
                "binary_sensor_problem",
                "lock_child_lock",
                "number_timer",
                "select_initial_state",
                "select_light",
                "sensor_current",
                "sensor_energy",
                "sensor_power",
                "sensor_voltage",
                "switch_overcharge_cutoff",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[TEST_DPS] = 21
        self.dps[ERROR_DPS] = 26
        self.dps[CYCLE_DPS] = "1A2B"
        self.dps[RANDOM_DPS] = "3C4D"

        self.assertDictEqual(
            self.multiSwitch["switch_outlet"].extra_state_attributes,
            {
                "test_bit": 21,
                "fault_code": 26,
                "cycle_timer": "1A2B",
                "random_timer": "3C4D",
            },
        )

    def test_multi_sensor_extra_state_attributes(self):
        self.dps[CALIBV_DPS] = 22
        self.dps[CALIBI_DPS] = 23
        self.dps[CALIBP_DPS] = 24
        self.dps[CALIBE_DPS] = 25

        self.assertDictEqual(
            self.multiSensor["sensor_current"].extra_state_attributes,
            {"calibration": 23},
        )
        self.assertDictEqual(
            self.multiSensor["sensor_energy"].extra_state_attributes,
            {"calibration": 25},
        )
        self.assertDictEqual(
            self.multiSensor["sensor_power"].extra_state_attributes,
            {"calibration": 24},
        )
        self.assertDictEqual(
            self.multiSensor["sensor_voltage"].extra_state_attributes,
            {"calibration": 22},
        )
