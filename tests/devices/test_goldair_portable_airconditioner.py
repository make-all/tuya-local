from homeassistant.components.climate.const import (
    SWING_OFF,
    SWING_ON,
)

from ..const import GOLDAIR_PORTABLE_AIR_CONDITIONER_PAYLOAD
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DP = "1"
TEMPERATURE_DP = "2"
CURRENT_TEMPERATURE_DP = "3"
MODE_DP = "4"
FANMODE_DP = "5"
IONIZER_DP = "11"
SWINGH_DP = "15"
FAULT_DP = "20"
SLEEP_DP = "103"
ONTIMER_DP = "104"
OFFTIMER_DP = "105"
TEMPF_DP = "107"
CURTEMPF_DP = "108"
FEATURE_DP = "109"
SWINGV_DP = "110"


class TestGoldairPortableAir(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "goldair_portable_airconditioner.yaml",
            GOLDAIR_PORTABLE_AIR_CONDITIONER_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DP,
            self.subject,
            min=16.0,
            max=31.0,
        )
        self.mark_secondary(
            [
                "binary_sensor_problem",
                "binary_sensor_tank_full",
                "number_on_timer",
                "number_off_timer",
            ],
        )

    def test_swing_modes_with_vswing_unavailable(self):
        self.dps[FEATURE_DP] = 26
        self.assertCountEqual(self.subject.swing_modes, [])
        self.assertCountEqual(
            self.subject.swing_horizontal_modes, [SWING_OFF, SWING_ON]
        )

    def test_swing_modes_with_vswing_available(self):
        self.dps[FEATURE_DP] = 27
        self.assertCountEqual(self.subject.swing_modes, [SWING_OFF, SWING_ON])
        self.assertCountEqual(
            self.subject.swing_horizontal_modes, [SWING_OFF, SWING_ON]
        )

    def test_swing(self):
        self.dps[FEATURE_DP] = 27
        self.dps[SWINGH_DP] = "on"
        self.dps[SWINGV_DP] = True
        self.assertEqual(self.subject.swing_mode, SWING_ON)
        self.assertEqual(self.subject.swing_horizontal_mode, SWING_ON)
        self.dps[SWINGH_DP] = "off"
        self.assertEqual(self.subject.swing_horizontal_mode, SWING_OFF)
        self.dps[SWINGV_DP] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

    def test_available(self):
        """Override the base class, as this has availability logic."""
        pass
