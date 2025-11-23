"""Tests for a simple switch with timer"""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import UnitOfTime

from ..const import TIMED_SOCKET_PAYLOAD
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "11"


class TestTimedSwitch(BasicNumberTests, SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("simple_switch_timer.yaml", TIMED_SOCKET_PAYLOAD)
        self.subject = self.entities.get("switch")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440,
            scale=60,
            unit=UnitOfTime.MINUTES,
            device_class=NumberDeviceClass.DURATION,
        )
        self.mark_secondary(["number_timer", "time_timer"])

    def test_extra_state_attributes_set(self):
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {},
        )
