"""Tests for the Logicom Strippy 4-way+USB powerstrip."""

from homeassistant.components.switch import SwitchDeviceClass

from ..const import LOGICOM_STRIPPY_PAYLOAD
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
SWITCH3_DPS = "3"
SWITCH4_DPS = "4"
SWITCHUSB_DPS = "5"
TIMER1_DPS = "9"
TIMER2_DPS = "10"
TIMER3_DPS = "11"
TIMER4_DPS = "12"
TIMERUSB_DPS = "13"


class TestLogicomPowerstrip(
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("logicom_powerstrip.yaml", LOGICOM_STRIPPY_PAYLOAD)
        self.setUpMultiSwitch(
            [
                {
                    "dps": SWITCH1_DPS,
                    "name": "switch_outlet_1",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH2_DPS,
                    "name": "switch_outlet_2",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH3_DPS,
                    "name": "switch_outlet_3",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH4_DPS,
                    "name": "switch_outlet_4",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCHUSB_DPS,
                    "name": "switch_usb_switch",
                    "device_class": SwitchDeviceClass.SWITCH,
                },
            ]
        )
        self.mark_secondary(
            [
                "time_timer_1",
                "time_timer_2",
                "time_timer_3",
                "time_timer_4",
                "time_timer_usb",
            ]
        )
