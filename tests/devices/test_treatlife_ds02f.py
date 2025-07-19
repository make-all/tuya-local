from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import UnitOfTime

from ..const import TREATLIFE_DS02F_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "2"
SPEED_DPS = "3"


class TestTreatlifeFan(SwitchableTests, BasicNumberTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("treatlife_ds02_fan.yaml", TREATLIFE_DS02F_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            scale=60,
            device_class=NumberDeviceClass.DURATION,
            unit=UnitOfTime.MINUTES,
        )
        self.mark_secondary(["number_timer", "time_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF,
        )

    def test_speed(self):
        self.dps[SPEED_DPS] = "level_2"
        self.assertEqual(self.subject.percentage, 50)

    def test_speed_step(self):
        self.assertEqual(self.subject.percentage_step, 25)
        self.assertEqual(self.subject.speed_count, 4)

    async def test_set_speed(self):
        async with assert_device_properties_set(
            self.subject._device, {SPEED_DPS: "level_3"}
        ):
            await self.subject.async_set_percentage(75)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(
            self.subject._device, {SPEED_DPS: "level_1"}
        ):
            await self.subject.async_set_percentage(30)
