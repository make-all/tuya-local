from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import UnitOfTime

from ..const import TMWF02_FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "2"
LEVEL_DPS = "3"
SPEED_DPS = "4"


class TestTMWF02Fan(BasicNumberTests, SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("tmwf02_fan.yaml", TMWF02_FAN_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440,
            scale=60,
            device_class=NumberDeviceClass.DURATION,
            unit=UnitOfTime.MINUTES,
        )
        self.mark_secondary(["number_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF,
        )

    def test_speed(self):
        self.dps[SPEED_DPS] = 35
        self.assertEqual(self.subject.percentage, 35)

    def test_speed_step(self):
        self.assertEqual(self.subject.percentage_step, 1)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 70}):
            await self.subject.async_set_percentage(70)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 25}):
            await self.subject.async_set_percentage(24.8)

    def test_extra_state_attributes(self):
        self.dps[LEVEL_DPS] = "level_3"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"fan_level": "level_3"},
        )
