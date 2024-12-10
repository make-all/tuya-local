"""Tests for Digoo DSSP202 dual switch with timers and energy monitoring"""

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTime,
)

from ..const import DIGOO_DGSP202_SOCKET_PAYLOAD
from ..mixins.number import MultiNumberTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
TIMER1_DPS = "9"
TIMER2_DPS = "10"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"


class TestDigooDGSP202Switch(
    MultiNumberTests, MultiSensorTests, MultiSwitchTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("digoo_dgsp202.yaml", DIGOO_DGSP202_SOCKET_PAYLOAD)
        self.setUpMultiSwitch(
            [
                {
                    "dps": SWITCH1_DPS,
                    "name": "switch_outlet_1",
                    "device_class": SwitchDeviceClass.OUTLET,
                    "power_dps": POWER_DPS,
                    "power_scale": 10,
                },
                {
                    "dps": SWITCH2_DPS,
                    "name": "switch_outlet_2",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
            ]
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": TIMER1_DPS,
                    "name": "number_timer_1",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMER2_DPS,
                    "name": "number_timer_2",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                },
            ]
        )
        self.setUpMultiSensors(
            [
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
                "number_timer_1",
                "number_timer_2",
                "sensor_voltage",
                "sensor_current",
                "sensor_power",
            ]
        )
