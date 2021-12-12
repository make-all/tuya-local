"""Tests for a simple switch with timer"""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET
from homeassistant.const import TIME_MINUTES

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
            unit=TIME_MINUTES,
        )
        self.mark_secondary(["number_timer"])

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_extra_state_attributes_set(self):
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {},
        )
