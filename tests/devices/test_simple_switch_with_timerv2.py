"""Tests for a simple switch with timer"""
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import UnitOfTime

from ..const import TIMED_SOCKETV2_PAYLOAD
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "9"


class TestTimedSwitch(BasicNumberTests, SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("simple_switch_timerv2.yaml", TIMED_SOCKETV2_PAYLOAD)
        self.subject = self.entities.get("switch")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440,
            scale=60,
            unit=UnitOfTime.MINUTES,
        )
        self.mark_secondary(["number_timer", "select_power_on_state"])

    def test_extra_state_attributes_set(self):
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {},
        )
