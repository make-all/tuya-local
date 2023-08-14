"""Tests for the switch entity."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTime,
)

from ..const import KOGAN_SOCKET_PAYLOAD
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "2"
CURRENT_DPS = "4"
POWER_DPS = "5"
VOLTAGE_DPS = "6"
OVERCURRENT_DPS = "7"


class TestKoganSwitch(
    BasicBinarySensorTests,
    BasicNumberTests,
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("smartplugv1.yaml", KOGAN_SOCKET_PAYLOAD)
        self.subject = self.entities.get("switch_outlet")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicBinarySensor(
            OVERCURRENT_DPS,
            self.entities.get("binary_sensor_overcurrent_alarm"),
            device_class=BinarySensorDeviceClass.PROBLEM,
        )
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=UnitOfTime.MINUTES,
            scale=60,
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
                "binary_sensor_overcurrent_alarm",
                "number_timer",
                "sensor_current",
                "sensor_power",
                "sensor_voltage",
            ]
        )

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, SwitchDeviceClass.OUTLET)
