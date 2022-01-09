"""Tests for the SmartMCB SMT006 Energy Meter"""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HEAT,
    DEVICE_CLASS_PLUG,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_PROBLEM,
    DEVICE_CLASS_SAFETY,
    DEVICE_CLASS_SMOKE,
)
from homeassistant.components.sensor import (
    STATE_CLASS_TOTAL,
    STATE_CLASS_TOTAL_INCREASING,
)
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR,
)

from ..const import SMARTMCB_SMT006_METER_PAYLOAD
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.number import BasicNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

TOTALENERGY_DPS = "1"
PHASEA_DPS = "6"
PHASEB_DPS = "7"
PHASEC_DPS = "8"
ERROR_DPS = "9"
PREPAY_DPS = "11"
RESET_DPS = "12"
BALANCE_DPS = "13"
CHARGE_DPS = "14"
SWITCH_DPS = "16"
SERIAL_DPS = "19"


class TestSmartMcbSMT006EnergyMeter(
    MultiBinarySensorTests,
    BasicNumberTests,
    BasicSelectTests,
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
            ],
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_energy",
                    "dps": TOTALENERGY_DPS,
                    "device_class": DEVICE_CLASS_ENERGY,
                    "unit": ENERGY_KILO_WATT_HOUR,
                    "state_class": STATE_CLASS_TOTAL_INCREASING,
                    "testdata": (123456, 1234.56),
                },
                {
                    "name": "sensor_balance_energy",
                    "dps": BALANCE_DPS,
                    "device_class": DEVICE_CLASS_ENERGY,
                    "unit": ENERGY_KILO_WATT_HOUR,
                    "state_class": STATE_CLASS_TOTAL,
                    "testdata": (123456, 1234.56),
                },
            ],
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "name": "binary_sensor_short_circuit",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (1, 0),
                },
                {
                    "name": "binary_sensor_surge",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (2, 0),
                },
                {
                    "name": "binary_sensor_overload",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (4, 0),
                },
                {
                    "name": "binary_sensor_leakage_current",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_SAFETY,
                    "testdata": (8, 0),
                },
                {
                    "name": "binary_sensor_high_temperature",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_HEAT,
                    "testdata": (16, 0),
                },
                {
                    "name": "binary_sensor_fire",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_SMOKE,
                    "testdata": (32, 0),
                },
                {
                    "name": "binary_sensor_high_power",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_POWER,
                    "testdata": (64, 0),
                },
                {
                    "name": "binary_sensor_self_test",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (128, 0),
                },
                {
                    "name": "binary_sensor_overcurrent",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (256, 0),
                },
                {
                    "name": "binary_sensor_unbalanced",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (512, 0),
                },
                {
                    "name": "binary_sensor_overvoltage",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (1024, 0),
                },
                {
                    "name": "binary_sensor_undervoltage",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (2048, 0),
                },
                {
                    "name": "binary_sensor_phase_fault",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (4096, 0),
                },
                {
                    "name": "binary_sensor_outage",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_POWER,
                    "testdata": (0, 8192),
                },
                {
                    "name": "binary_sensor_magnetism",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PROBLEM,
                    "testdata": (16384, 0),
                },
                {
                    "name": "binary_sensor_low_credit",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_BATTERY,
                    "testdata": (32768, 0),
                },
                {
                    "name": "binary_sensor_credit",
                    "dps": ERROR_DPS,
                    "device_class": DEVICE_CLASS_PLUG,
                    "testdata": (0, 65536),
                    "unit": ENERGY_KILO_WATT_HOUR,
                },
            ],
        )
        self.setUpBasicNumber(
            CHARGE_DPS,
            self.entities.get("number_charge_energy"),
            max=9999.99,
            scale=100,
            step=0.01,
        )
        self.setUpBasicSelect(
            RESET_DPS,
            self.entities.get("select_energy_reset"),
            {
                "": "",
                "empty": "Reset",
            },
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
                "number_charge_energy",
                "select_energy_reset",
                "sensor_balance_energy",
                "switch_prepay",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[PHASEA_DPS] = "Phase A"
        self.dps[PHASEB_DPS] = "Phase B"
        self.dps[PHASEC_DPS] = "Phase C"
        self.dps[SERIAL_DPS] = "Breaker Number"

        self.assertDictEqual(
            self.multiSwitch["switch"].extra_state_attributes,
            {
                "phase_a": "Phase A",
                "phase_b": "Phase B",
                "phase_c": "Phase C",
                "breaker_number": "Breaker Number",
            },
        )
