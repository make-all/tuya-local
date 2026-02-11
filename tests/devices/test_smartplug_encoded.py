"""Tests for the switch entity."""

from homeassistant.components.switch import SwitchDeviceClass

from ..const import SMARTPLUG_ENCODED_PAYLOAD
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "11"
RANDOM_DPS = "101"
CIRCULATE_DPS = "102"
SCHEDULE_DPS = "103"


class TestSwitchEncoded(SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("smartplug_encoded.yaml", SMARTPLUG_ENCODED_PAYLOAD)
        self.subject = self.entities.get("switch_outlet")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.mark_secondary(["time_timer"])

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, SwitchDeviceClass.OUTLET)
