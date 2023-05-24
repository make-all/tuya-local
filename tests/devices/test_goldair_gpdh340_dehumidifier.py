from ..const import GOLDAIR_GPDH340_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DP = "1"
MODE_DP = "2"
HUMIDITY_DP = "4"
FAN_DP = "6"
ERROR_DP = "11"
CURRENTTEMP_DP = "103"
CURRENTHUMID_DP = "104"
MODEL_DP = "105"
CHILDLOCK_DP = "106"
DISPLAY_DP = "107"
FILTERCLEAN_DP = "108"
PUMP_DP = "109"


class TestGPDH340Dehumidifier(SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "goldair_gpdh340_dehumidifier.yaml", GOLDAIR_GPDH340_PAYLOAD
        )
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(SWITCH_DP, self.subject)

        self.mark_secondary(
            [
                "light_front_display",
                "lock_child_lock",
                "binary_sensor_tank",
                "binary_sensor_fault",
                "binary_sensor_filter_clean_required",
            ]
        )

    def test_available_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            ["Sleeping space", "Living space", "Basement", "Continuous"],
        )

    def test_mode(self):
        self.dps[MODE_DP] = "2"
        self.assertEqual(self.subject.mode, "Custom")
        self.dps[MODE_DP] = "4"
        self.assertEqual(self.subject.mode, "Sleeping space")
        self.dps[MODE_DP] = "5"
        self.assertEqual(self.subject.mode, "Living space")
        self.dps[MODE_DP] = "6"
        self.assertEqual(self.subject.mode, "Basement")
        self.dps[MODE_DP] = "7"
        self.assertEqual(self.subject.mode, "Continuous")

    async def test_async_set_mode(self):
        async with assert_device_properties_set(self.subject._device, {MODE_DP: "6"}):
            await self.subject.async_set_mode("Basement")
