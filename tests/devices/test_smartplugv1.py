"""Tests for the switch entity."""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET

from ..const import KOGAN_SOCKET_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import SwitchableTests, TuyaDeviceTestCase

SWITCH_DPS = "1"
TIMER_DPS = "2"
CURRENT_DPS = "4"
POWER_DPS = "5"
VOLTAGE_DPS = "6"


class TestKoganSwitch(SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("smartplugv1.yaml", KOGAN_SOCKET_PAYLOAD)
        self.subject = self.entities.get("switch")
        self.setUpSwitchable(SWITCH_DPS, self.subject)

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_current_power_w(self):
        self.dps[POWER_DPS] = 1234
        self.assertEqual(self.subject.current_power_w, 123.4)

    def test_device_state_attributes_set(self):
        self.dps[TIMER_DPS] = 1
        self.dps[VOLTAGE_DPS] = 2350
        self.dps[CURRENT_DPS] = 1234
        self.dps[POWER_DPS] = 5678
        self.assertDictEqual(
            self.subject.device_state_attributes,
            {
                "timer": 1,
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
            },
        )
