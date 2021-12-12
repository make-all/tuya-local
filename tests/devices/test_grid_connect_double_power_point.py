"""Tests for the switch entity."""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET
from homeassistant.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    ELECTRIC_CURRENT_MILLIAMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_WATT_HOUR,
    POWER_WATT,
    TIME_SECONDS,
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
                    "device_class": DEVICE_CLASS_OUTLET,
                },
                {
                    "name": "switch_outlet_2",
                    "dps": SWITCH2_DPS,
                    "device_class": DEVICE_CLASS_OUTLET,
                },
                {
                    "name": "switch_master",
                    "dps": MASTER_DPS,
                    "device_class": DEVICE_CLASS_OUTLET,
                    "power_dps": POWER_DPS,
                    "power_scale": 10,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_energy",
                    "dps": ENERGY_DPS,
                    "device_class": DEVICE_CLASS_ENERGY,
                    "unit": ENERGY_WATT_HOUR,
                    "state_class": "total_increasing",
                },
                {
                    "name": "sensor_current",
                    "dps": CURRENT_DPS,
                    "device_class": DEVICE_CLASS_CURRENT,
                    "unit": ELECTRIC_CURRENT_MILLIAMPERE,
                    "state_class": "measurement",
                },
                {
                    "name": "sensor_power",
                    "dps": POWER_DPS,
                    "device_class": DEVICE_CLASS_POWER,
                    "unit": POWER_WATT,
                    "state_class": "measurement",
                    "testdata": (1234, 123.4),
                },
                {
                    "name": "sensor_voltage",
                    "dps": VOLTAGE_DPS,
                    "device_class": DEVICE_CLASS_VOLTAGE,
                    "unit": ELECTRIC_POTENTIAL_VOLT,
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
                    "unit": TIME_SECONDS,
                },
                {
                    "name": "number_timer_2",
                    "dps": COUNTDOWN2_DPS,
                    "max": 86400,
                    "unit": TIME_SECONDS,
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

    async def test_turn_on_fails_when_master_is_off(self):
        self.dps[MASTER_DPS] = False
        self.dps[SWITCH1_DPS] = False
        self.dps[SWITCH2_DPS] = False
        with self.assertRaises(AttributeError):
            await self.multiSwitch["switch_outlet_1"].async_turn_on()
        with self.assertRaises(AttributeError):
            await self.multiSwitch["switch_outlet_2"].async_turn_on()

    # Since we have attributes, override the default test which expects none.
    def test_multi_switch_state_attributes(self):
        self.dps[COUNTDOWN1_DPS] = 9
        self.dps[COUNTDOWN2_DPS] = 10
        self.dps[VOLTAGE_DPS] = 2350
        self.dps[CURRENT_DPS] = 1234
        self.dps[POWER_DPS] = 5678
        self.dps[TEST_DPS] = 21
        self.dps[CALIBV_DPS] = 22
        self.dps[CALIBA_DPS] = 23
        self.dps[CALIBW_DPS] = 24
        self.dps[CALIBE_DPS] = 25
        self.assertDictEqual(
            self.multiSwitch["switch_master"].extra_state_attributes,
            {
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
                "test_bit": 21,
                "voltage_calibration": 22,
                "current_calibration": 23,
                "power_calibration": 24,
                "energy_calibration": 25,
            },
        )
        self.assertDictEqual(
            self.multiSwitch["switch_outlet_1"].extra_state_attributes,
            {
                "countdown": 9,
            },
        )
        self.assertDictEqual(
            self.multiSwitch["switch_outlet_2"].extra_state_attributes,
            {
                "countdown": 10,
            },
        )
