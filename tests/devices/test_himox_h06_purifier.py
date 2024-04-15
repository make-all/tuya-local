from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTime

from ..const import HIMOX_H06_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.button import BasicButtonTests
from ..mixins.light import BasicLightTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import SwitchableTests
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
    BasicButtonTests,
    BasicLightTests,
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
        self.setUpBasicButton(
            RESET_DPS,
            self.entities.get("button_filter_reset"),
            ButtonDeviceClass.RESTART,
        )
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
        self.setUpMultiSensors(
            [
                {
                    "dps": FILTER_DPS,
                    "name": "sensor_active_filter_life",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": COUNTDOWN_DPS,
                    "name": "sensor_time_remaining",
                    "unit": UnitOfTime.MINUTES,
                    "device_class": SensorDeviceClass.DURATION,
                },
                {
                    "dps": AQI_DPS,
                    "name": "sensor_air_quality",
                },
            ]
        )
        self.mark_secondary(
            [
                "button_filter_reset",
                "light_aq_indicator",
                "sensor_active_filter_life",
                "select_timer",
                "sensor_time_remaining",
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
