"""Tests for the energy monitoring powerstrip."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)

from ..const import ENERGY_POWERSTRIP_PAYLOAD
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DP = "1"
SWITCH2_DP = "2"
SWITCH3_DP = "3"
SWITCH4_DP = "4"
CURRENT_DP = "102"
POWER_DP = "103"
VOLTAGE_DP = "104"
UNKNOWN105_DP = "105"
UNKNOWN106_DP = "106"
UNKNOWN107_DP = "107"
UNKNOWN108_DP = "108"
UNKNOWN109_DP = "109"


class TestEnergyMonitoringPowerstrip(
    MultiSensorTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "energy_monitoring_powerstrip.yaml", ENERGY_POWERSTRIP_PAYLOAD
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": SWITCH1_DP,
                    "name": "switch_switch_1",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH2_DP,
                    "name": "switch_switch_2",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH3_DP,
                    "name": "switch_switch_3",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH4_DP,
                    "name": "switch_switch_4",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_current",
                    "dps": CURRENT_DP,
                    "device_class": SensorDeviceClass.CURRENT,
                    "unit": UnitOfElectricCurrent.MILLIAMPERE,
                    "state_class": SensorStateClass.MEASUREMENT,
                },
                {
                    "name": "sensor_power",
                    "dps": POWER_DP,
                    "device_class": SensorDeviceClass.POWER,
                    "unit": UnitOfPower.WATT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": (1234, 123.4),
                },
                {
                    "name": "sensor_voltage",
                    "dps": VOLTAGE_DP,
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "unit": UnitOfElectricPotential.VOLT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "testdata": (2345, 234.5),
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_current",
                "sensor_power",
                "sensor_voltage",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[UNKNOWN105_DP] = 105
        self.dps[UNKNOWN106_DP] = 106
        self.dps[UNKNOWN107_DP] = 107
        self.dps[UNKNOWN108_DP] = 108
        self.dps[UNKNOWN109_DP] = 109
        for k, v in self.multiSwitch.items():
            if k == "switch_switch_1":
                self.assertDictEqual(
                    v.extra_state_attributes,
                    {
                        "unknown_105": 105,
                        "unknown_106": 106,
                        "unknown_107": 107,
                        "unknown_108": 108,
                        "unknown_109": 109,
                    },
                )
            else:
                self.assertEqual(v.extra_state_attributes, {})
