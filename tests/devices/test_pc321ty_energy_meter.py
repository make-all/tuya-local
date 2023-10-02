"""Tests for the PC321-TY Power Clamp Energy meter"""
from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    SensorDeviceClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

from ..const import PC321TY_POWERCLAMP_PAYLOAD
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

VOLTAGE1_DP = "101"
CURRENT1_DP = "102"
POWER1_DP = "103"
PFACTOR1_DP = "104"
ENERGY1_DP = "106"
VOLTAGE2_DP = "111"
CURRENT2_DP = "112"
POWER2_DP = "113"
PFACTOR2_DP = "114"
ENERGY2_DP = "116"
VOLTAGE3_DP = "121"
CURRENT3_DP = "122"
POWER3_DP = "123"
PFACTOR3_DP = "124"
ENERGY3_DP = "126"
TOTALENERGY_DP = "131"
TOTALCURRENT_DP = "132"
TOTALPOWER_DP = "133"
FREQUENCY_DP = "135"
TEMPERATURE_DP = "136"


class TestPC321TYPowerClamp(MultiSensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "pc321ty_energy_meter.yaml",
            PC321TY_POWERCLAMP_PAYLOAD,
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": TOTALENERGY_DP,
                    "name": "sensor_energy",
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "device_class": SensorDeviceClass.ENERGY,
                    "state_class": STATE_CLASS_TOTAL_INCREASING,
                    "testdata": (12345, 123.45),
                },
                {
                    "dps": VOLTAGE1_DP,
                    "name": "sensor_voltage_a",
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (2348, 234.8),
                },
                {
                    "dps": CURRENT1_DP,
                    "name": "sensor_current_a",
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (4567, 4.567),
                },
                {
                    "dps": POWER1_DP,
                    "name": "sensor_power_a",
                    "unit": UnitOfPower.WATT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "device_class": SensorDeviceClass.POWER,
                },
                {
                    "dps": PFACTOR1_DP,
                    "name": "sensor_power_factor_a",
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (5000, 50.00),
                },
                {
                    "dps": ENERGY1_DP,
                    "name": "sensor_energy_a",
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "testdata": (12345, 123.45),
                },
                {
                    "dps": VOLTAGE2_DP,
                    "name": "sensor_voltage_b",
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (2348, 234.8),
                },
                {
                    "dps": CURRENT2_DP,
                    "name": "sensor_current_b",
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (4567, 4.567),
                },
                {
                    "dps": POWER2_DP,
                    "name": "sensor_power_b",
                    "unit": UnitOfPower.WATT,
                    "device_class": SensorDeviceClass.POWER,
                    "state_class": STATE_CLASS_MEASUREMENT,
                },
                {
                    "dps": PFACTOR2_DP,
                    "name": "sensor_power_factor_b",
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (5000, 50.00),
                },
                {
                    "dps": ENERGY2_DP,
                    "name": "sensor_energy_b",
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "testdata": (12345, 123.45),
                },
                {
                    "dps": VOLTAGE3_DP,
                    "name": "sensor_voltage_c",
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (2348, 234.8),
                },
                {
                    "dps": CURRENT3_DP,
                    "name": "sensor_current_c",
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (4567, 4.567),
                },
                {
                    "dps": POWER3_DP,
                    "name": "sensor_power_c",
                    "unit": UnitOfPower.WATT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "device_class": SensorDeviceClass.POWER,
                },
                {
                    "dps": PFACTOR3_DP,
                    "name": "sensor_power_factor_c",
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (5000, 50.00),
                },
                {
                    "dps": ENERGY3_DP,
                    "name": "sensor_energy_c",
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "testdata": (12345, 123.45),
                },
                {
                    "dps": TOTALCURRENT_DP,
                    "name": "sensor_total_current",
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (12345, 12.345),
                },
                {
                    "dps": TOTALPOWER_DP,
                    "name": "sensor_total_active_power",
                    "unit": UnitOfPower.WATT,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "device_class": SensorDeviceClass.POWER,
                },
                {
                    "dps": FREQUENCY_DP,
                    "name": "sensor_frequency",
                    "unit": UnitOfFrequency.HERTZ,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "device_class": SensorDeviceClass.FREQUENCY,
                },
                {
                    "dps": TEMPERATURE_DP,
                    "name": "sensor_temperature",
                    "unit": UnitOfTemperature.CELSIUS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "testdata": (234, 23.4),
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_voltage_a",
                "sensor_current_a",
                "sensor_power_a",
                "sensor_power_factor_a",
                "sensor_energy_a",
                "sensor_voltage_b",
                "sensor_current_b",
                "sensor_power_b",
                "sensor_power_factor_b",
                "sensor_energy_b",
                "sensor_voltage_c",
                "sensor_current_c",
                "sensor_power_c",
                "sensor_power_factor_c",
                "sensor_energy_c",
                "sensor_total_current",
                "sensor_total_active_power",
                "sensor_frequency",
                "sensor_temperature",
            ]
        )
