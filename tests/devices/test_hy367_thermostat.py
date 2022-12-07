from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from ..mixins.climate import TargetTemperatureTests
from ..mixins.number import BasicNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase


TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"

# DPS: {'2': 190, '3': 210, '4': 'auto', '7': False, '44': 0, '103': 25, '105': 900, '107': 20, '108': 17, '109': 0, '114': 15, '116': True
DEFAULTS = {
    "2": 190,
    "3": 210,
}

class TestHY367Thermostat(
    BasicNumberTests,
    BasicSelectTests,
    BasicSensorTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True
    def setUp(self):
        self.setUpForConfig("hy367_thermostat.yaml", DEFAULTS)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(TEMPERATURE_DPS, self.subject)


    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )
    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 240
        self.assertEqual(self.subject.current_temperature, 24)
