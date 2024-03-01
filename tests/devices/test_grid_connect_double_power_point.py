"""Tests for the switch entity."""

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)

from ..const import GRIDCONNECT_2SOCKET_PAYLOAD
from ..mixins.lock import BasicLockTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
COUNTDOWN1_DPS = "9"
COUNTDOWN2_DPS = "10"
ENERGY_DPS = "17"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"
TEST_DPS = "21"
CALIBV_DPS = "22"
CALIBA_DPS = "23"
CALIBW_DPS = "24"
CALIBE_DPS = "25"
INITIAL_DPS = "38"
LOCK_DPS = "40"
MASTER_DPS = "101"


class TestGridConnectDoubleSwitch(
    BasicLockTests,
    BasicSelectTests,
    MultiNumberTests,
    MultiSensorTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "grid_connect_usb_double_power_point.yaml",
            GRIDCONNECT_2SOCKET_PAYLOAD,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSelect(
            INITIAL_DPS,
            self.entities.get("select_initial_state"),
            {
                "on": "On",
                "off": "Off",
                "memory": "Last State",
            },
        )
        # Master switch must go last, otherwise its tests interfere with
        # the tests for the other switches since it overrides them.
        # Tests for the specific override behaviour are below.
        self.setUpMultiSwitch(
            [
                {
                    "name": "switch_outlet_1",
                    "dps": SWITCH1_DPS,
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "name": "switch_outlet_2",
                    "dps": SWITCH2_DPS,
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "name": "switch_master",
                    "dps": MASTER_DPS,
                    "device_class": SwitchDeviceClass.OUTLET,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_energy",
                    "dps": ENERGY_DPS,
                    "unit": UnitOfEnergy.WATT_HOUR,
                },
                {
                    "name": "sensor_current",
                    "dps": CURRENT_DPS,
                    "device_class": SensorDeviceClass.CURRENT,
                    "unit": UnitOfElectricCurrent.MILLIAMPERE,
                    "state_class": "measurement",
                },
                {
                    "name": "sensor_power",
                    "dps": POWER_DPS,
                    "device_class": SensorDeviceClass.POWER,
                    "unit": UnitOfPower.WATT,
                    "state_class": "measurement",
                    "testdata": (1234, 123.4),
                },
                {
                    "name": "sensor_voltage",
                    "dps": VOLTAGE_DPS,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "unit": UnitOfElectricPotential.VOLT,
                    "state_class": "measurement",
                    "testdata": (2345, 234.5),
                },
            ]
        )
        self.setUpMultiNumber(
            [
                {
                    "name": "number_timer_1",
                    "dps": COUNTDOWN1_DPS,
                    "max": 86400,
                    "unit": UnitOfTime.SECONDS,
                },
                {
                    "name": "number_timer_2",
                    "dps": COUNTDOWN2_DPS,
                    "max": 86400,
                    "unit": UnitOfTime.SECONDS,
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "number_timer_1",
                "number_timer_2",
                "select_initial_state",
                "switch_master",
                "sensor_energy",
                "sensor_current",
                "sensor_power",
                "sensor_voltage",
            ],
        )

    # Since we have attributes, override the default test which expects none.
    def test_multi_switch_state_attributes(self):
        self.dps[TEST_DPS] = 21
        self.assertDictEqual(
            self.multiSwitch["switch_master"].extra_state_attributes,
            {
                "test_bit": 21,
            },
        )

    def test_multi_sensor_extra_state_attributes(self):
        self.dps[CALIBA_DPS] = 1
        self.dps[CALIBE_DPS] = 2
        self.dps[CALIBV_DPS] = 3
        self.dps[CALIBW_DPS] = 4

        self.assertDictEqual(
            self.multiSensor["sensor_current"].extra_state_attributes,
            {"calibration": 1},
        )
        self.assertDictEqual(
            self.multiSensor["sensor_energy"].extra_state_attributes,
            {"calibration": 2},
        )
        self.assertDictEqual(
            self.multiSensor["sensor_voltage"].extra_state_attributes,
            {"calibration": 3},
        )
        self.assertDictEqual(
            self.multiSensor["sensor_power"].extra_state_attributes,
            {"calibration": 4},
        )
