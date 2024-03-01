"""Tests for the ES01 powerstrip."""

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import UnitOfTime

from ..const import ES01_POWERSTRIP_PAYLOAD
from ..mixins.number import MultiNumberTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
SWITCH3_DPS = "3"
SWITCHUSB_DPS = "4"
TIMER1_DPS = "5"
TIMER2_DPS = "6"
TIMER3_DPS = "7"
TIMERUSB_DPS = "8"


class TestES01Powerstrip(
    MultiNumberTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("es01_powerstrip.yaml", ES01_POWERSTRIP_PAYLOAD)
        self.setUpMultiSwitch(
            [
                {
                    "dps": SWITCH1_DPS,
                    "name": "switch_switch_1",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH2_DPS,
                    "name": "switch_switch_2",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {
                    "dps": SWITCH3_DPS,
                    "name": "switch_switch_3",
                    "device_class": SwitchDeviceClass.OUTLET,
                },
                {"dps": SWITCHUSB_DPS, "name": "switch_usb_switch"},
            ]
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": TIMER1_DPS,
                    "name": "number_timer_socket_1",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMER2_DPS,
                    "name": "number_timer_socket_2",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMER3_DPS,
                    "name": "number_timer_socket_3",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMERUSB_DPS,
                    "name": "number_usb_timer",
                    "max": 1440,
                    "scale": 60,
                    "unit": UnitOfTime.MINUTES,
                },
            ]
        )
        self.mark_secondary(
            [
                "number_timer_socket_1",
                "number_timer_socket_2",
                "number_timer_socket_3",
                "number_usb_timer",
            ]
        )
