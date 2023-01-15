from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase


TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"

# DPS: {'2': 190, '3': 210, '4': 'auto', '7': False, '44': 0, '103': 25, '105': 900, '107': 20, '108': 17, '109': 0, '114': 15, '116': True
DEFAULTS = {
    "2": 190,
    "3": 210,
    "4": "auto",
    "7": False,
    "44": 0,
    "103": 25,
    "105": 900,
    "107": 20,
    "108": 17,
    "109": 0,
    "114": 15,
    "116": True,
}


class TestHY367Thermostat(
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("hy367_thermostat.yaml", DEFAULTS)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS, self.subject, scale=10, step=5, min=16.0, max=70.0
        )

        self.mark_secondary(
            [
                "lock_key_lock",
                "number_maximum_temperature",
                "number_boos_mode",
                "number_comfort_temperature",
                "number_energy_saving_temperature",
                "number_min_temperature",
                "lock_child_lock",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 240
        self.assertEqual(self.subject.current_temperature, 24)
