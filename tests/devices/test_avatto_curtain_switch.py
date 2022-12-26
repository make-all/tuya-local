"""Tests for the Avatto roller blinds controller."""

from ..const import AVATTO_CURTAIN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.select import BasicSelectTests
from ..mixins.button import MultiButtonTests
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DP = "1"
BACKLIGHT_DP = "101"


class TestAvattoCurtainSwitch(
    MultiButtonTests, BasicSelectTests, BasicLightTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("avatto_curtain_switch.yaml", AVATTO_CURTAIN_PAYLOAD)
        self.setUpMultiButtons(
            [
                {
                    "dps": COMMAND_DP,
                    "name": "button_stop",
                    "testdata": "stop",
                },
                {
                    "dps": COMMAND_DP,
                    "name": "button_open",
                    "testdata": "open",
                },
                {
                    "dps": COMMAND_DP,
                    "name": "button_close",
                    "testdata": "close",
                },
            ]
        )
        self.setUpBasicSelect(
            COMMAND_DP,
            self.entities.get("select"),
            {
                "stop": "Stop",
                "open": "Open",
                "close": "Close",
            },
        ),
        self.setUpBasicLight(
            BACKLIGHT_DP,
            self.entities.get("light_backlight"),
        )
        self.mark_secondary(["select", "light_backlight"])
