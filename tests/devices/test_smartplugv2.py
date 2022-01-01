"""Tests for the switch entity."""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET
from homeassistant.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    ELECTRIC_CURRENT_MILLIAMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    POWER_WATT,
    TIME_MINUTES,
)

from ..const import KOGAN_SOCKET_PAYLOAD2
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "9"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"


class TestSwitchV2(
    BasicNumberTests, MultiSensorTests, SwitchableTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("smartplugv2.yaml", KOGAN_SOCKET_PAYLOAD2)
        self.subject = self.entities.get("switch")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=TIME_MINUTES,
            scale=60,
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_voltage",
                    "dps": VOLTAGE_DPS,
                    "unit": ELECTRIC_POTENTIAL_VOLT,
                    "device_class": DEVICE_CLASS_VOLTAGE,
                    "state_class": "measurement",
                    "testdata": (2300, 230.0),
                },
                {
                    "name": "sensor_current",
                    "dps": CURRENT_DPS,
                    "unit": ELECTRIC_CURRENT_MILLIAMPERE,
                    "device_class": DEVICE_CLASS_CURRENT,
                    "state_class": "measurement",
                },
                {
                    "name": "sensor_power",
                    "dps": POWER_DPS,
                    "unit": POWER_WATT,
                    "device_class": DEVICE_CLASS_POWER,
                    "state_class": "measurement",
                    "testdata": (1234, 123.4),
                },
            ]
        )
        self.mark_secondary(
            [
                "number_timer",
                "sensor_current",
                "sensor_power",
                "sensor_voltage",
            ]
        )

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_current_power_w(self):
        self.dps[POWER_DPS] = 1234
        self.assertEqual(self.subject.current_power_w, 123.4)

    def test_extra_state_attributes_set(self):
        self.dps[TIMER_DPS] = 1
        self.dps[VOLTAGE_DPS] = 2350
        self.dps[CURRENT_DPS] = 1234
        self.dps[POWER_DPS] = 5678
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "timer": 1,
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
            },
        )
