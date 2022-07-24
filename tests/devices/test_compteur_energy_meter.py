"""Tests for the Compteur Energy meter"""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
)
from homeassistant.const import (
    ELECTRIC_CURRENT_AMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
)

from ..const import COMPTEUR_SMARTMETER_PAYLOAD
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase


ENERGY_DP = "17"
CURRENT_DP = "18"
POWER_DP = "19"
VOLTAGE_DP = "20"
UNKNOWN21_DP = "21"
UNKNOWN22_DP = "22"
UNKNOWN23_DP = "23"
UNKNOWN24_DP = "24"
UNKNOWN25_DP = "25"
UNKNOWN26_DP = "26"


class TestCompteurEnergyMeter(MultiSensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "compteur_energy_meter.yaml",
            COMPTEUR_SMARTMETER_PAYLOAD,
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": ENERGY_DP,
                    "name": "sensor",
                    "unit": ENERGY_KILO_WATT_HOUR,
                    "device_class": SensorDeviceClass.ENERGY,
                    "state_class": STATE_CLASS_TOTAL_INCREASING,
                    "testdata": (12345, 12.345),
                },
                {
                    "dps": VOLTAGE_DP,
                    "name": "sensor_voltage",
                    "unit": ELECTRIC_POTENTIAL_VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (2348, 234.8),
                },
                {
                    "dps": CURRENT_DP,
                    "name": "sensor_current",
                    "unit": ELECTRIC_CURRENT_AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (4567, 4.567),
                },
                {
                    "dps": POWER_DP,
                    "name": "sensor_power",
                    "unit": POWER_WATT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "device_class": SensorDeviceClass.POWER,
                    "testdata": (890, 89.0),
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_voltage",
                "sensor_current",
                "sensor_power",
            ]
        )

    def test_multi_sensor_extra_state_attributes(self):
        self.dps[UNKNOWN21_DP] = 21
        self.dps[UNKNOWN22_DP] = 22
        self.dps[UNKNOWN23_DP] = 23
        self.dps[UNKNOWN24_DP] = 24
        self.dps[UNKNOWN25_DP] = 25
        self.dps[UNKNOWN26_DP] = 26

        for k, v in self.multiSensor.items():
            if k == "sensor":
                self.assertDictEqual(
                    v.extra_state_attributes,
                    {
                        "unknown_21": 21,
                        "unknown_22": 22,
                        "unknown_23": 23,
                        "unknown_24": 24,
                        "unknown_25": 25,
                        "unknown_26": 26,
                    },
                )
            else:
                self.assertEqual(v.extra_state_attributes, {})
