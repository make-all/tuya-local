"""Tests for the Logicom Strippy 4-way+USB powerstrip."""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import UnitOfTime

from ..const import LOGICOM_STRIPPY_PAYLOAD
from ..mixins.number import MultiNumberTests
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
    MultiNumberTests,
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
        self.setUpMultiNumber(
            [
                {
                    "dps": TIMER1_DPS,
                    "name": "number_timer_1",
                    "max": 1440,
                    "scale": 60,
                    "device_class": NumberDeviceClass.DURATION,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMER2_DPS,
                    "name": "number_timer_2",
                    "max": 1440,
                    "scale": 60,
                    "device_class": NumberDeviceClass.DURATION,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMER3_DPS,
                    "name": "number_timer_3",
                    "max": 1440,
                    "scale": 60,
                    "device_class": NumberDeviceClass.DURATION,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMER4_DPS,
                    "name": "number_timer_4",
                    "max": 1440,
                    "scale": 60,
                    "device_class": NumberDeviceClass.DURATION,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": TIMERUSB_DPS,
                    "name": "number_usb_timer",
                    "max": 1440,
                    "scale": 60,
                    "device_class": NumberDeviceClass.DURATION,
                    "unit": UnitOfTime.MINUTES,
                },
            ]
        )
        self.mark_secondary(
            [
                "number_timer_1",
                "number_timer_2",
                "number_timer_3",
                "number_timer_4",
                "number_usb_timer",
            ]
        )
