"""Tests for Parkside PLGS 2012 A1 Smart Charger"""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
)

from ..const import PARKSIDE_PLGS2012A1_PAYLOAD
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
NAME_DPS = "2"
CURRENT_DPS = "3"
VOLTAGE_DPS = "4"
BATTERY_DPS = "5"
TEMPERATURE_DPS = "6"
MODE_DPS = "7"
STORAGE_DPS = "8"
LIMITER_DPS = "9"
MAXTEMPCOUNT_DPS = "10"
FAULT_DPS = "11"
MAXCURRENT_DPS = "101"
REMAIN_DPS = "102"
ALMOSTCHARGED_DPS = "103"
FULLYCHARGED_DPS = "104"


class TestParksidePLGS2012A1Charger(
    MultiBinarySensorTests,
    MultiNumberTests,
    BasicSelectTests,
    MultiSensorTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "parkside_plgs2012a1_smart_charger.yaml", PARKSIDE_PLGS2012A1_PAYLOAD
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "name": "binary_sensor_almost_charged",
                    "dps": ALMOSTCHARGED_DPS,
                },
                {
                    "name": "binary_sensor_fully_charged",
                    "dps": FULLYCHARGED_DPS,
                },
                {
                    "name": "binary_sensor_fault",
                    "dps": FAULT_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (32, 0),
                },
            ],
        )
        self.setUpMultiNumber(
            [
                {
                    "name": "number_charge_current",
                    "dps": CURRENT_DPS,
                    "device_class": NumberDeviceClass.CURRENT,
                    "max": 30.000,
                    "step": 0.1,
                    "scale": 1000,
                    "unit": UnitOfElectricCurrent.AMPERE,
                },
                {
                    "name": "number_charge_voltage",
                    "dps": VOLTAGE_DPS,
                    "device_class": NumberDeviceClass.VOLTAGE,
                    "max": 25.0,
                    "scale": 1000,
                    "step": 0.1,
                    "unit": UnitOfElectricPotential.VOLT,
                },
            ],
        )
        self.setUpBasicSelect(
            MODE_DPS,
            self.entities.get("select_charge_type"),
            {
                "ECO": "Eco",
                "quick": "Performance",
                "standard": "Balanced",
                "individual": "Expert",
            },
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_battery",
                    "dps": BATTERY_DPS,
                    "unit": PERCENTAGE,
                    "device_class": SensorDeviceClass.BATTERY,
                },
                {
                    "name": "sensor_time_remaining",
                    "dps": REMAIN_DPS,
                    "unit": UnitOfTime.MINUTES,
                    "device_class": SensorDeviceClass.DURATION,
                },
                {
                    "name": "sensor_temperature",
                    "dps": TEMPERATURE_DPS,
                    "unit": UnitOfTemperature.CELSIUS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                },
                {
                    "name": "sensor_max_current",
                    "dps": MAXCURRENT_DPS,
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "device_class": SensorDeviceClass.CURRENT,
                    "testdata": (1234, 1.234),
                },
                {
                    "name": "sensor_max_temperature_count",
                    "dps": MAXTEMPCOUNT_DPS,
                },
            ],
        )
        self.setUpMultiSwitch(
            [
                {
                    "name": "switch",
                    "dps": SWITCH_DPS,
                },
                {
                    "name": "switch_storage",
                    "dps": STORAGE_DPS,
                },
                {
                    "name": "switch_temperature_limiter",
                    "dps": LIMITER_DPS,
                },
            ],
        )

        self.mark_secondary(
            [
                "number_charge_current",
                "number_charge_voltage",
                "switch_storage",
                "switch_temperature_limiter",
                "sensor_temperature",
                "sensor_max_temperature_count",
                "select_charge_type",
                "sensor_max_current",
                "binary_sensor_almost_charged",
                "binary_sensor_fully_charged",
                "binary_sensor_fault",
            ]
        )

    def test_multi_switch_state_attributes(self):
        switch = self.multiSwitch.get("switch")
        storage = self.multiSwitch.get("switch_storage")
        temp = self.multiSwitch.get("switch_temperature_limiter")
        self.assertEqual(storage.extra_state_attributes, {})
        self.assertEqual(temp.extra_state_attributes, {})
        self.dps[FAULT_DPS] = 32
        self.dps[NAME_DPS] = "test"
        self.assertDictEqual(
            switch.extra_state_attributes, {"model": "test", "fault_code": 32}
        )
