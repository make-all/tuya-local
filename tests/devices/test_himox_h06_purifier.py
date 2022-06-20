from homeassistant.components.fan import FanEntityFeature
from homeassistant.const import (
    PERCENTAGE,
    TIME_MINUTES,
)

from ..const import HIMOX_H06_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
SPEED_DPS = "4"
FILTER_DPS = "5"
LIGHT_DPS = "8"
RESET_DPS = "11"
TIMER_DPS = "18"
COUNTDOWN_DPS = "19"
AQI_DPS = "22"
MODE_DPS = "101"


class TestHimoxH06Purifier(
    BasicLightTests,
    BasicSwitchTests,
    MultiSelectTests,
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("himox_h06_purifier.yaml", HIMOX_H06_PURIFIER_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_aq_indicator"))
        self.setUpMultiSelect(
            [
                {
                    "dps": TIMER_DPS,
                    "name": "select_timer",
                    "options": {
                        "cancel": "Off",
                        "4h": "4 hours",
                        "8h": "8 hours",
                    },
                },
                {
                    "dps": MODE_DPS,
                    "name": "select_configuration",
                    "options": {
                        "calcle": "Auto",
                        "1": "Medium",
                        "2": "Severe",
                    },
                },
            ]
        )
        self.setUpBasicSwitch(RESET_DPS, self.entities.get("switch_filter_reset"))
        self.setUpMultiSensors(
            [
                {
                    "dps": FILTER_DPS,
                    "name": "sensor_active_filter_life",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": COUNTDOWN_DPS,
                    "name": "sensor_timer",
                    "unit": TIME_MINUTES,
                },
                {
                    "dps": AQI_DPS,
                    "name": "sensor_air_quality",
                },
            ]
        )
        self.mark_secondary(
            [
                "light_aq_indicator",
                "switch_filter_reset",
                "sensor_active_filter_life",
                "select_timer",
                "sensor_timer",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            FanEntityFeature.SET_SPEED,
        )

    def test_speed(self):
        self.dps[SPEED_DPS] = "low"
        self.assertEqual(self.subject.percentage, 33)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 33, 0)

    async def test_set_speed(self):
        async with assert_device_properties_set(
            self.subject._device, {SPEED_DPS: "mid"}
        ):
            await self.subject.async_set_percentage(67)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(
            self.subject._device, {SPEED_DPS: "high"}
        ):
            await self.subject.async_set_percentage(90)
