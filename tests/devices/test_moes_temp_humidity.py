from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import MOES_TEMP_HUMID_PAYLOAD
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

MAINSW_DPS = "1"
SW1_DPS = "2"
SW2_DPS = "3"
MODE_DPS = "4"
TEMP_DPS = "6"
HIGHTEMPSW_DPS = "8"
HIGHTEMPAL_DPS = "9"
LOWTEMPSW_DPS = "11"
LOWTEMPAL_DPS = "12"
CALIB_DPS = "18"
HUMIDITY_DPS = "20"
MAXHUMID_DPS = "21"
MINHUMID_DPS = "22"
CYCLE_DPS = "24"
RULE1_DPS = "101"
RULE2_DPS = "102"
TIMER1_DPS = "103"
TIMER2_DPS = "104"
INIT_DPS = "105"
UNKNOWN106_DPS = "106"


class TestMoesTempHumidity(
    BasicSensorTests,
    MultiNumberTests,
    MultiSelectTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("moes_temp_humidity.yaml", MOES_TEMP_HUMID_PAYLOAD)
        self.setUpBasicSensor(
            TEMP_DPS,
            self.entities.get("sensor_temperature"),
            unit=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class="measurement",
            testdata=(251, 25.1),
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": CALIB_DPS,
                    "name": "number_temperature_calibration",
                    "min": -9.0,
                    "max": 9.0,
                    "scale": 10,
                    "step": 0.1,
                },
                {
                    "dps": TIMER1_DPS,
                    "name": "number_timer_1",
                    "max": 86400,
                    "unit": UnitOfTime.SECONDS,
                },
                {
                    "dps": TIMER2_DPS,
                    "name": "number_timer_2",
                    "max": 86400,
                    "unit": UnitOfTime.SECONDS,
                },
            ]
        )
        self.setUpMultiSelect(
            [
                {
                    "dps": MODE_DPS,
                    "name": "select_mode",
                    "options": {
                        "auto": "Auto",
                        "manual": "Manual",
                    },
                },
                {
                    "dps": INIT_DPS,
                    "name": "select_power_on_state",
                    "options": {
                        "on": "On",
                        "off": "Off",
                        "memory": "Last State",
                    },
                },
            ]
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": MAINSW_DPS,
                    "name": "switch_main_switch",
                },
                {
                    "dps": SW1_DPS,
                    "name": "switch_switch_1",
                },
                {
                    "dps": SW2_DPS,
                    "name": "switch_switch_2",
                },
            ]
        )
        self.mark_secondary(
            [
                "switch_main_switch",
                "select_mode",
                "number_temperature_calibration",
                "number_maximum_humidity",
                "number_minimum_humidity",
                "number_timer_1",
                "number_timer_2",
                "select_power_on_state",
                "number_high_temperature_switch_level",
                "switch_high_temperature_switch",
                "number_high_temperature_alarm_level",
                "number_low_temperature_switch_level",
                "switch_low_temperature_switch",
                "number_low_temperature_alarm_level",
                "binary_sensor_problem",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[CYCLE_DPS] = "ABCDEF0123456789"
        self.dps[UNKNOWN106_DPS] = "unknown106"
        self.dps[RULE1_DPS] = "rules for switch 1"
        self.dps[RULE2_DPS] = "rules for switch 2"

        self.assertDictEqual(
            self.multiSwitch["switch_main_switch"].extra_state_attributes,
            {
                "fault_code": "OK",
                "cycle_time": "ABCDEF0123456789",
                "unknown_106": "unknown106",
            },
        )
        self.assertDictEqual(
            self.multiSwitch["switch_switch_1"].extra_state_attributes,
            {"auto_rules": "rules for switch 1"},
        )
        self.assertDictEqual(
            self.multiSwitch["switch_switch_2"].extra_state_attributes,
            {"auto_rules": "rules for switch 2"},
        )
