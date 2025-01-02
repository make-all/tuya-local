"""Tests for multiple sensors encoded together in a single dp."""

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)

from ..const import TOMPD63LW_SOCKET_PAYLOAD
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

ENERGY_DP = "1"
PHASEA_DP = "6"
FAULT_DP = "9"
PREPAY_DP = "11"
RESET_DP = "12"
BALANCE_DP = "13"
CHARGE_DP = "14"
LEAKAGE_DP = "15"
SWITCH_DP = "16"
ALARM1_DP = "17"
ALARM2_DP = "18"
IDNUM_DP = "19"
TEST_DP = "21"


class TestTOMPD63lw(MultiSensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("tompd_63lw_breaker.yaml", TOMPD63LW_SOCKET_PAYLOAD)
        self.subject = self.entities.get("switch")
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_voltage",
                    "dps": PHASEA_DP,
                    "unit": UnitOfElectricPotential.VOLT,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "testdata": ("CPwAFGEAAu4=", 230.0),
                },
                {
                    "name": "sensor_current",
                    "dps": PHASEA_DP,
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "testdata": ("CPwAFGEAAu4=", 5.217),
                },
                {
                    "name": "sensor_power",
                    "dps": PHASEA_DP,
                    "unit": UnitOfPower.KILO_WATT,
                    "device_class": SensorDeviceClass.POWER,
                    "testdata": ("CPwAFGEAAu4=", 0.75),
                },
            ]
        )
        self.mark_secondary(
            [
                "binary_sensor_problem",
                "button_clear_energy",
                "button_earth_leak_test",
                "button_energy_reset",
                "button_factory_reset",
                "button_refresh_sensors",
                "number_charge_energy",
                "sensor_balance_energy",
                "sensor_current",
                "sensor_frequency",
                "sensor_leakage_current",
                "sensor_power",
                "sensor_power_factor",
                "sensor_voltage",
                "switch_prepayment",
            ]
        )

    def test_phasea_encoding(self):
        self.dps[PHASEA_DP] = "CQQAFGkAAu4="
        self.assertEqual(self.multiSensor["sensor_voltage"].native_value, 230.8)
        self.assertEqual(self.multiSensor["sensor_current"].native_value, 5.225)
        self.assertEqual(self.multiSensor["sensor_power"].native_value, 0.75)

    def test_phasea_missing(self):
        self.dps[PHASEA_DP] = None
        self.assertIsNone(self.multiSensor["sensor_voltage"].native_value)
        self.assertIsNone(self.multiSensor["sensor_current"].native_value)
        self.assertIsNone(self.multiSensor["sensor_power"].native_value)
