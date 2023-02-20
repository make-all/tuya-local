from homeassistant.components.fan import FanEntityFeature

from ..const import BLITZWOLF_BWSH2_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.select import MultiSelectTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DP = "1"
SPEED_DP = "3"
LIGHT_DP = "6"
TIMER_DP = "19"


class TestBlitzwolfSH2Humidifier(MultiSelectTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "blitzwolf_bwsh2_humidifier.yaml",
            BLITZWOLF_BWSH2_PAYLOAD,
        )
        self.subject = self.entities.get("fan")
        self.setUpMultiSelect(
            [
                {
                    "name": "select_light",
                    "dps": LIGHT_DP,
                    "options": {
                        "close": "Off",
                        "purple": "Purple",
                        "blue": "Blue",
                        "cyan": "Cyan",
                        "green": "Green",
                        "yellow": "Yellow",
                        "orange": "Orange",
                        "red": "Red",
                        "colour": "Colorful",
                    },
                },
                {
                    "name": "select_timer",
                    "dps": TIMER_DP,
                    "options": {
                        "cancel": "Off",
                        "2h": "2 hours",
                        "4h": "4 hours",
                        "6h": "6 hours",
                        "8h": "8 hours",
                        "10h": "10 hours",
                        "12h": "12 hours",
                    },
                },
            ]
        )
        self.mark_secondary(["select_light", "select_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            FanEntityFeature.SET_SPEED,
        )

    def test_speed(self):
        self.dps[SPEED_DP] = "sleep"
        self.assertEqual(self.subject.percentage, 10)
        self.dps[SPEED_DP] = "grade1"
        self.assertEqual(self.subject.percentage, 25)
        self.dps[SPEED_DP] = "grade2"
        self.assertEqual(self.subject.percentage, 40)
        self.dps[SPEED_DP] = "grade3"
        self.assertEqual(self.subject.percentage, 55)
        self.dps[SPEED_DP] = "grade4"
        self.assertEqual(self.subject.percentage, 70)
        self.dps[SPEED_DP] = "grade5"
        self.assertEqual(self.subject.percentage, 85)
        self.dps[SPEED_DP] = "grade6"
        self.assertEqual(self.subject.percentage, 100)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SPEED_DP: "grade3"},
        ):
            await self.subject.async_set_percentage(50)
