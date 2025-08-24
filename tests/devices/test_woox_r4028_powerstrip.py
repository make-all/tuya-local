"""Tests for the Woox R4028 powerstrip."""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import UnitOfTime

from ..const import WOOX_R4028_SOCKET_PAYLOAD
from ..mixins.number import MultiNumberTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
SWITCH3_DPS = "3"
SWITCHUSB_DPS = "7"
TIMER1_DPS = "101"
TIMER2_DPS = "102"
TIMER3_DPS = "103"
TIMERUSB_DPS = "105"


class TestWooxR4028Powerstrip(
    MultiNumberTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("woox_r4028_powerstrip.yaml", WOOX_R4028_SOCKET_PAYLOAD)
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
                    "dps": SWITCHUSB_DPS,
                    "name": "switch_usb_switch",
                    "device_class": SwitchDeviceClass.SWITCH,
                },
            ]
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": TIMER1_DPS,
                    "name": "number_timer_1",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                    "device_class": NumberDeviceClass.DURATION,
                },
                {
                    "dps": TIMER2_DPS,
                    "name": "number_timer_2",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                    "device_class": NumberDeviceClass.DURATION,
                },
                {
                    "dps": TIMER3_DPS,
                    "name": "number_timer_3",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                    "device_class": NumberDeviceClass.DURATION,
                },
                {
                    "dps": TIMERUSB_DPS,
                    "name": "number_usb_timer",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                    "device_class": NumberDeviceClass.DURATION,
                },
            ]
        )
        self.mark_secondary(
            [
                "number_timer_1",
                "number_timer_2",
                "number_timer_3",
                "number_usb_timer",
                "time_timer_1",
                "time_timer_2",
                "time_timer_3",
                "time_timer_usb",
            ]
        )
