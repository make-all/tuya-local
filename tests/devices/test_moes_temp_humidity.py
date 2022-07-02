from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import TEMP_CELSIUS, TIME_SECONDS

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
UNKNOWN8_DPS = "8"
UNKNOWN9_DPS = "9"
UNKNOWN11_DPS = "11"
UNKNOWN12_DPS = "12"
CALIB_DPS = "18"
UNKNOWN20_DPS = "20"
UNKNOWN21_DPS = "21"
UNKNOWN22_DPS = "22"
UNKNOWN24_DPS = "24"
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
            self.entities.get("sensor_current_temperature"),
            unit=TEMP_CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class="measurement",
            testdata=(251, 25.1),
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": CALIB_DPS,
                    "name": "number_temperature_calibration",
                    "min": -9.9,
                    "max": 9.9,
                    "scale": 10,
                    "step": 0.1,
                },
                {
                    "dps": TIMER1_DPS,
                    "name": "number_timer_1",
                    "max": 86400,
                    "unit": TIME_SECONDS,
                },
                {
                    "dps": TIMER2_DPS,
                    "name": "number_timer_2",
                    "max": 86400,
                    "unit": TIME_SECONDS,
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
                "number_timer_1",
                "number_timer_2",
                "select_power_on_state",
            ]
        )

    def test_multi_switch_state_attributes(self):
        self.dps[UNKNOWN8_DPS] = True
        self.dps[UNKNOWN9_DPS] = 9
        self.dps[UNKNOWN11_DPS] = False
        self.dps[UNKNOWN12_DPS] = 12
        self.dps[UNKNOWN20_DPS] = 20
        self.dps[UNKNOWN21_DPS] = 21
        self.dps[UNKNOWN22_DPS] = 22
        self.dps[UNKNOWN24_DPS] = "unknown24"
        self.dps[UNKNOWN106_DPS] = "unknown106"
        self.dps[RULE1_DPS] = "rules for switch 1"
        self.dps[RULE2_DPS] = "rules for switch 2"

        self.assertDictEqual(
            self.multiSwitch["switch_main_switch"].extra_state_attributes,
            {
                "unknown_8": True,
                "unknown_9": 9,
                "unknown_11": False,
                "unknown_12": 12,
                "unknown_20": 20,
                "unknown_21": 21,
                "unknown_22": 22,
                "unknown_24": "unknown24",
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
