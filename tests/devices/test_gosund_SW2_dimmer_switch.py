"""Tests for the switch entity."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass

from ..const import GOSUND_DUMMER_SWITCH_PAYLOAD
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
BRIGHTNESS_DPS = "3"
TEMPERATURE_DPS = "101"


class TestGosundSwitch(
    BasicBinarySensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("gosund_SW2_dimmer_switch.yaml", GOSUND_DUMMER_SWITCH_PAYLOAD)
        self.subject = self.entities.get("light")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicBinarySensor(
            TEMPERATURE_DPS,
            self.entities.get("binary_sensor_temperature_alarm"),
            device_class=BinarySensorDeviceClass.PROBLEM,
        )

        self.mark_secondary(["binary_sensor_temperature_alarm"])

    def test_device_class_is_light(self):
        self.assertEqual(self.subject.device_class, SwitchDeviceClass.LIGHT)

    def test_switch_is_on(self):
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.light.is_on)
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.light.is_on)

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = 50
        self.assertAlmostEqual(self.light.brightness, 129, 0)
