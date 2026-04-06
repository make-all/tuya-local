"""Tests for TOMZN SWC32v4 breaker (up to three-phase base64 sensors + energy)."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)

from ..const import TOMZN_SWC32V4_BREAKER_PAYLOAD
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

ENERGY_DP = "1"
PHASEA_DP = "6"
PHASEB_DP = "7"
PHASEC_DP = "8"
LEAKAGE_DP = "15"
SWITCH_DP = "16"
TEMP_DP = "102"


class TestTomznSwc32v4Breaker(
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    def setUp(self):
        self.setUpForConfig(
            "tomzn_swc32v4_breaker.yaml",
            TOMZN_SWC32V4_BREAKER_PAYLOAD,
        )
        self.subject = self.entities.get("switch")
        self.setUpSwitchable(SWITCH_DP, self.subject)
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_total_energy",
                    "dps": ENERGY_DP,
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "device_class": SensorDeviceClass.ENERGY,
                    "state_class": SensorStateClass.TOTAL_INCREASING,
                    "testdata": (123450, 1234.5),
                },
                {
                    "name": "sensor_phase_a_voltage",
                    "dps": PHASEA_DP,
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 230.0),
                },
                {
                    "name": "sensor_phase_a_current",
                    "dps": PHASEA_DP,
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 5.217),
                },
                {
                    "name": "sensor_phase_a_power",
                    "dps": PHASEA_DP,
                    "unit": UnitOfPower.KILO_WATT,
                    "device_class": SensorDeviceClass.POWER,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 0.75),
                },
                {
                    "name": "sensor_phase_b_voltage",
                    "dps": PHASEB_DP,
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 230.0),
                },
                {
                    "name": "sensor_phase_b_current",
                    "dps": PHASEB_DP,
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 5.217),
                },
                {
                    "name": "sensor_phase_b_power",
                    "dps": PHASEB_DP,
                    "unit": UnitOfPower.KILO_WATT,
                    "device_class": SensorDeviceClass.POWER,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 0.75),
                },
                {
                    "name": "sensor_phase_c_voltage",
                    "dps": PHASEC_DP,
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 230.0),
                },
                {
                    "name": "sensor_phase_c_current",
                    "dps": PHASEC_DP,
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 5.217),
                },
                {
                    "name": "sensor_phase_c_power",
                    "dps": PHASEC_DP,
                    "unit": UnitOfPower.KILO_WATT,
                    "device_class": SensorDeviceClass.POWER,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": ("CPwAFGEAAu4=", 0.75),
                },
                {
                    "name": "sensor_leakage_current",
                    "dps": LEAKAGE_DP,
                    "unit": "mA",
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": (42, 42),
                },
                {
                    "name": "sensor_temperature",
                    "dps": TEMP_DP,
                    "unit": UnitOfTemperature.CELSIUS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": (255, 25.5),
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_total_energy",
                "sensor_phase_a_voltage",
                "sensor_phase_a_current",
                "sensor_phase_a_power",
                "sensor_phase_b_voltage",
                "sensor_phase_b_current",
                "sensor_phase_b_power",
                "sensor_phase_c_voltage",
                "sensor_phase_c_current",
                "sensor_phase_c_power",
                "sensor_leakage_current",
                "sensor_temperature",
            ]
        )

    def test_phase_a_encoding(self):
        self.dps[PHASEA_DP] = "CQQAFGkAAu4="
        self.assertEqual(self.multiSensor["sensor_phase_a_voltage"].native_value, 230.8)
        self.assertEqual(self.multiSensor["sensor_phase_a_current"].native_value, 5.225)
        self.assertEqual(self.multiSensor["sensor_phase_a_power"].native_value, 0.75)

    def test_phase_b_encoding(self):
        self.dps[PHASEB_DP] = "CQQAFGkAAu4="
        self.assertEqual(self.multiSensor["sensor_phase_b_voltage"].native_value, 230.8)
        self.assertEqual(self.multiSensor["sensor_phase_b_current"].native_value, 5.225)
        self.assertEqual(self.multiSensor["sensor_phase_b_power"].native_value, 0.75)

    def test_phase_c_encoding(self):
        self.dps[PHASEC_DP] = "CQQAFGkAAu4="
        self.assertEqual(self.multiSensor["sensor_phase_c_voltage"].native_value, 230.8)
        self.assertEqual(self.multiSensor["sensor_phase_c_current"].native_value, 5.225)
        self.assertEqual(self.multiSensor["sensor_phase_c_power"].native_value, 0.75)

    def test_phase_a_missing(self):
        self.dps[PHASEA_DP] = None
        self.assertIsNone(self.multiSensor["sensor_phase_a_voltage"].native_value)
        self.assertIsNone(self.multiSensor["sensor_phase_a_current"].native_value)
        self.assertIsNone(self.multiSensor["sensor_phase_a_power"].native_value)

    def test_phase_b_missing(self):
        self.dps[PHASEB_DP] = None
        self.assertIsNone(self.multiSensor["sensor_phase_b_voltage"].native_value)
        self.assertIsNone(self.multiSensor["sensor_phase_b_current"].native_value)
        self.assertIsNone(self.multiSensor["sensor_phase_b_power"].native_value)

    def test_phase_c_missing(self):
        self.dps[PHASEC_DP] = None
        self.assertIsNone(self.multiSensor["sensor_phase_c_voltage"].native_value)
        self.assertIsNone(self.multiSensor["sensor_phase_c_current"].native_value)
        self.assertIsNone(self.multiSensor["sensor_phase_c_power"].native_value)
