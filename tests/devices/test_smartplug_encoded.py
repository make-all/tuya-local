"""Tests for the switch entity."""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import UnitOfTime

from ..const import SMARTPLUG_ENCODED_PAYLOAD
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "11"
RANDOM_DPS = "101"
CIRCULATE_DPS = "102"
SCHEDULE_DPS = "103"


class TestSwitchEncoded(BasicNumberTests, SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("smartplug_encoded.yaml", SMARTPLUG_ENCODED_PAYLOAD)
        self.subject = self.entities.get("switch_outlet")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440.0,
            unit=UnitOfTime.MINUTES,
            device_class=NumberDeviceClass.DURATION,
            scale=60,
        )
        self.mark_secondary(["number_timer"])

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, SwitchDeviceClass.OUTLET)

    def test_extra_state_attributes_set(self):
        self.dps[RANDOM_DPS] = "101"
        self.dps[CIRCULATE_DPS] = "102"
        self.dps[SCHEDULE_DPS] = "103"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "random": "101",
                "circulate": "102",
                "schedule": "103",
            },
        )
