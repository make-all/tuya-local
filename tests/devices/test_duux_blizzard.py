from homeassistant.components.climate.const import HVACMode

from ..const import DUUX_BLIZZARD_PAYLOAD
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DP = "1"
MODE_DP = "2"
SPEED_DP = "3"
TIMER_DP = "4"
TEMPERATURE_DP = "5"
SLEEP_DP = "6"
ION_DP = "7"
CURRENTTEMP_DP = "8"
FAULT_DP = "9"
SETTEMPF_DP = "10"
CURTEMPF_DP = "11"
IONSHOW_DP = "12"
HEATSHOW_DP = "13"
UNIT_DP = "14"
COUNTDOWN_DP = "15"


class TestDuuxBlizzard(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "duux_blizzard_portable_aircon.yaml",
            DUUX_BLIZZARD_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.ionizer = self.entities.get("switch_ionizer")
        self.setUpTargetTemperature(
            TEMPERATURE_DP,
            self.subject,
            min=18.0,
            max=32.0,
        )
        self.mark_secondary(
            [
                "number_timer",
                "switch_sleep",
                "switch_ionizer",
                "binary_sensor_tank_full",
                "binary_sensor_problem",
                "select_temperature_unit",
                "sensor_time_remaining",
            ]
        )

    def test_hvac_modes_with_heat_disabled(self):
        self.dps[HEATSHOW_DP] = False
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
                HVACMode.AUTO,
            ],
        )

    def test_hvac_modes_with_heat_enabled(self):
        self.dps[HEATSHOW_DP] = True
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
                HVACMode.AUTO,
                HVACMode.HEAT,
            ],
        )

    def test_ionizer_availability(self):
        self.dps[IONSHOW_DP] = False
        self.dps[ION_DP] = True
        self.assertFalse(self.ionizer.available)
        self.dps[IONSHOW_DP] = True
        self.assertTrue(self.ionizer.available)
