from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.const import UnitOfTime

from ..const import TG_ELECTRO_SENSOR_PAYLOAD
from ..mixins.select import MultiSelectTests
from ..mixins.number import MultiNumberTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

PIR_SENSOR_DPS = "51"
SWITCH_DPS = "20"
LUX_DPS = "53"
PROX_DPS = "54"
TIME_DPS = "55"


class TestTgElectroMotionSensor(BasicSwitchTests, MultiSelectTests, MultiNumberTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("tg_electro_motion_sensor.yaml", TG_ELECTRO_SENSOR_PAYLOAD)
        self.subject = self.entities.get("light")
        self.auto_sw = self.entities.get("switch_pir_sensor")
        self.setUpMultiSelect(
            [
                {
                    "dps": LUX_DPS,
                    "name": "select_ambient_light",
                    "options": {
                        "5lux": "dark",
                        "10lux": "late_evening",
                        "50lux": "evening",
                        "300lux": "early_evening",
                        "2000lux": "day",
                    }
                },
                {
                    "dps": PROX_DPS,
                    "name": "select_sensitivity",
                    "options": {
                        "low": "low",
                        "middle": "middle",
                        "high": "high"
                    }
                }
            ]
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": TIME_DPS,
                    "name": "number_light_duration",
                    "device_class": NumberDeviceClass.DURATION,
                    "min": 5,
                    "max": 360,
                    "step": 10,
                    "unit": UnitOfTime.SECONDS,
                }
            ]
        )
        self.mark_secondary(
            [
                "number_light_duration",
                "select_ambient_light",
                "select_sensitivity",
            ]
        )

    def test_is_on_reflects_switch(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    def test_auto_mode_is_on(self):
        self.dps[SWITCH_DPS] = False
        self.dps[PIR_SENSOR_DPS] = "auto"
        self.assertTrue(self.auto_sw.is_on)
        self.assertFalse(self.subject.is_on)
        self.dps[PIR_SENSOR_DPS] = "manual"
        self.assertFalse(self.auto_sw.is_on)
        self.assertFalse(self.subject.is_on)
        self.dps[SWITCH_DPS] = True
        self.dps[PIR_SENSOR_DPS] = "auto"
        self.assertTrue(self.auto_sw.is_on)
        self.assertTrue(self.subject.is_on)
        self.dps[PIR_SENSOR_DPS] = "manual"
        self.assertFalse(self.auto_sw.is_on)
        self.assertTrue(self.subject.is_on)

