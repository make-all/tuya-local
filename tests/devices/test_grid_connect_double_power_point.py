"""Tests for the switch entity."""
from homeassistant.components.switch import DEVICE_CLASS_OUTLET

from ..const import GRIDCONNECT_2SOCKET_PAYLOAD
from ..mixins.lock import BasicLockTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH1_DPS = "1"
SWITCH2_DPS = "2"
COUNTDOWN1_DPS = "9"
COUNTDOWN2_DPS = "10"
UNKNOWN17_DPS = "17"
CURRENT_DPS = "18"
POWER_DPS = "19"
VOLTAGE_DPS = "20"
UNKNOWN21_DPS = "21"
UNKNOWN22_DPS = "22"
UNKNOWN23_DPS = "23"
UNKNOWN24_DPS = "24"
UNKNOWN25_DPS = "25"
UNKNOWN38_DPS = "38"
LOCK_DPS = "40"
MASTER_DPS = "101"


class TestGridConnectDoubleSwitch(
    BasicLockTests,
    MultiSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "grid_connect_usb_double_power_point.yaml",
            GRIDCONNECT_2SOCKET_PAYLOAD,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        # Master switch must go last, otherwise its tests interfere with
        # the tests for the other switches since it overrides them.
        # Tests for the specific override behaviour are below.
        self.setUpMultiSwitch(
            [
                {
                    "name": "switch_outlet_1",
                    "dps": SWITCH1_DPS,
                    "device_class": DEVICE_CLASS_OUTLET,
                },
                {
                    "name": "switch_outlet_2",
                    "dps": SWITCH2_DPS,
                    "device_class": DEVICE_CLASS_OUTLET,
                },
                {
                    "name": "switch_master",
                    "dps": MASTER_DPS,
                    "device_class": DEVICE_CLASS_OUTLET,
                    "power_dps": POWER_DPS,
                    "power_scale": 10,
                },
            ]
        )

    async def test_turn_on_fails_when_master_is_off(self):
        self.dps[MASTER_DPS] = False
        self.dps[SWITCH1_DPS] = False
        self.dps[SWITCH2_DPS] = False
        with self.assertRaises(AttributeError):
            await self.multiSwitch["switch_outlet_1"].async_turn_on()
        with self.assertRaises(AttributeError):
            await self.multiSwitch["switch_outlet_2"].async_turn_on()

    # Since we have attributes, override the default test which expects none.
    def test_multi_switch_state_attributes(self):
        self.dps[COUNTDOWN1_DPS] = 9
        self.dps[COUNTDOWN2_DPS] = 10
        self.dps[UNKNOWN17_DPS] = 17
        self.dps[VOLTAGE_DPS] = 2350
        self.dps[CURRENT_DPS] = 1234
        self.dps[POWER_DPS] = 5678
        self.dps[UNKNOWN21_DPS] = 21
        self.dps[UNKNOWN22_DPS] = 22
        self.dps[UNKNOWN23_DPS] = 23
        self.dps[UNKNOWN24_DPS] = 24
        self.dps[UNKNOWN25_DPS] = 25
        self.dps[UNKNOWN38_DPS] = "38"
        self.assertDictEqual(
            self.multiSwitch["switch_master"].device_state_attributes,
            {
                "current_a": 1.234,
                "voltage_v": 235.0,
                "current_power_w": 567.8,
                "unknown_17": 17,
                "unknown_21": 21,
                "unknown_22": 22,
                "unknown_23": 23,
                "unknown_24": 24,
                "unknown_25": 25,
                "unknown_38": "38",
            },
        )
        self.assertDictEqual(
            self.multiSwitch["switch_outlet_1"].device_state_attributes,
            {
                "countdown": 9,
            },
        )
        self.assertDictEqual(
            self.multiSwitch["switch_outlet_2"].device_state_attributes,
            {
                "countdown": 10,
            },
        )
