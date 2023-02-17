"""Tests for the SmartMCB SMT006 Energy Meter"""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    STATE_CLASS_TOTAL,
    STATE_CLASS_TOTAL_INCREASING,
)
from homeassistant.const import UnitOfEnergy

from ..const import SMARTMCB_SMT006_METER_PAYLOAD
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.button import BasicButtonTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

TOTALENERGY_DPS = "1"
ERROR_DPS = "9"
PREPAY_DPS = "11"
RESET_DPS = "12"
BALANCE_DPS = "13"
SWITCH_DPS = "16"
SERIAL_DPS = "19"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"
UNKNOWN103_DPS = "103"
UNKNOWN104_DPS = "104"
UNKNOWN105_DPS = "105"
UNKNOWN106_DPS = "106"


class TestSmartMcbSMT006EnergyMeter(
    BasicButtonTests,
    MultiBinarySensorTests,
    MultiSensorTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "smartmcb_smt006_energymeter.yaml",
            SMARTMCB_SMT006_METER_PAYLOAD,
        )

        self.setUpBasicButton(
            RESET_DPS,
            self.entities.get("button_energy_reset"),
            ButtonDeviceClass.RESTART,
        )
        self.setUpMultiSwitch(
            [
                {
                    "name": "switch",
                    "dps": SWITCH_DPS,
                },
                {
                    "name": "switch_prepay",
                    "dps": PREPAY_DPS,
                },
                {
                    "name": "switch_energy_reset",
                    "dps": RESET_DPS,
                },
            ],
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_energy",
                    "dps": TOTALENERGY_DPS,
                    "device_class": SensorDeviceClass.ENERGY,
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "state_class": STATE_CLASS_TOTAL_INCREASING,
                    "testdata": (123456, 1234.56),
                },
                {
                    "name": "sensor_balance_energy",
                    "dps": BALANCE_DPS,
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "testdata": (123456, 1234.56),
                },
            ],
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "name": "binary_sensor_short_circuit",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (1, 0),
                },
                {
                    "name": "binary_sensor_surge",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (2, 0),
                },
                {
                    "name": "binary_sensor_overload",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (4, 0),
                },
                {
                    "name": "binary_sensor_leakage_current",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.SAFETY,
                    "testdata": (8, 0),
                },
                {
                    "name": "binary_sensor_high_temperature",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.HEAT,
                    "testdata": (16, 0),
                },
                {
                    "name": "binary_sensor_fire",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.SMOKE,
                    "testdata": (32, 0),
                },
                {
                    "name": "binary_sensor_high_power",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.POWER,
                    "testdata": (64, 0),
                },
                {
                    "name": "binary_sensor_self_test",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (128, 0),
                },
                {
                    "name": "binary_sensor_overcurrent",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (256, 0),
                },
                {
                    "name": "binary_sensor_unbalanced",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (512, 0),
                },
                {
                    "name": "binary_sensor_overvoltage",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (1024, 0),
                },
                {
                    "name": "binary_sensor_undervoltage",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (2048, 0),
                },
                {
                    "name": "binary_sensor_phase_fault",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (4096, 0),
                },
                {
                    "name": "binary_sensor_outage",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.POWER,
                    "testdata": (0, 8192),
                },
                {
                    "name": "binary_sensor_magnetism",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (16384, 0),
                },
                {
                    "name": "binary_sensor_low_credit",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.BATTERY,
                    "testdata": (32768, 0),
                },
                {
                    "name": "binary_sensor_credit",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PLUG,
                    "testdata": (0, 65536),
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                },
            ],
        )
        self.mark_secondary(
            [
                "binary_sensor_credit",
                "binary_sensor_fire",
                "binary_sensor_high_power",
                "binary_sensor_high_temperature",
                "binary_sensor_leakage_current",
                "binary_sensor_low_credit",
                "binary_sensor_magnetism",
                "binary_sensor_outage",
                "binary_sensor_overcurrent",
                "binary_sensor_overload",
                "binary_sensor_overvoltage",
                "binary_sensor_phase_fault",
                "binary_sensor_self_test",
                "binary_sensor_short_circuit",
                "binary_sensor_surge",
                "binary_sensor_unbalanced",
                "binary_sensor_undervoltage",
                "button_energy_reset",
                "sensor_balance_energy",
                "switch_energy_reset",
                "switch_prepay",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[SERIAL_DPS] = "Breaker Number"
        self.dps[UNKNOWN101_DPS] = 101
        self.dps[UNKNOWN102_DPS] = 102
        self.dps[UNKNOWN103_DPS] = 103
        self.dps[UNKNOWN104_DPS] = 104
        self.dps[UNKNOWN105_DPS] = True
        self.dps[UNKNOWN106_DPS] = False

        self.assertDictEqual(
            self.multiSwitch["switch"].extra_state_attributes,
            {
                "breaker_number": "Breaker Number",
                "unknown_101": 101,
                "unknown_102": 102,
                "unknown_103": 103,
                "unknown_104": 104,
                "unknown_105": True,
                "unknown_106": False,
            },
        )

    def test_multiple_concurrent_errors(self):
        self.dps[ERROR_DPS] = 15
        self.assertTrue(self.multiBSensor["binary_sensor_short_circuit"].is_on)
        self.assertTrue(self.multiBSensor["binary_sensor_surge"].is_on)
        self.assertTrue(self.multiBSensor["binary_sensor_overload"].is_on)
        self.assertTrue(self.multiBSensor["binary_sensor_leakage_current"].is_on)
        self.assertFalse(self.multiBSensor["binary_sensor_high_temperature"].is_on)
        self.assertFalse(self.multiBSensor["binary_sensor_fire"].is_on)
