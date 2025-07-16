"""Tests for a simple switch with timer"""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import UnitOfTime

from ..const import TIMED_SOCKETV2_PAYLOAD
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "9"
INITIAL_STATE_DPS = "38"


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
            device_class=NumberDeviceClass.DURATION,
            unit=UnitOfTime.MINUTES,
        )
        self.mark_secondary(["number_timer", "select_initial_state"])

    def test_extra_state_attributes_set(self):
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {},
        )

    def test_available(self):
        for id, e in self.entities.items():
            if id == "select_initial_state":
                self.dps[INITIAL_STATE_DPS] = None
                self.assertFalse(e.available)
                self.dps[INITIAL_STATE_DPS] = "on"
            self.assertTrue(e.available)
