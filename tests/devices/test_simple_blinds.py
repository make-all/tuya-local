"""Tests for the simple blinds controller."""

from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature

from ..const import SIMPLE_BLINDS_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DPS = "1"
POSITION_DPS = "2"
BACKMODE_DPS = "5"
ACTION_DPS = "7"


class TestSimpleBlinds(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("simple_blinds.yaml", SIMPLE_BLINDS_PAYLOAD)
        self.subject = self.entities["cover_blind"]

    def test_device_class_is_blind(self):
        self.assertEqual(self.subject.device_class, CoverDeviceClass.BLIND)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.SET_POSITION
                | CoverEntityFeature.STOP
            ),
        )

    def test_current_cover_position(self):
        self.dps[POSITION_DPS] = 47
        self.assertEqual(self.subject.current_cover_position, 53)

    def test_is_opening(self):
        self.dps[COMMAND_DPS] = "open"
        self.dps[POSITION_DPS] = 0
        self.assertFalse(self.subject.is_opening)
        self.dps[POSITION_DPS] = 50
        self.assertIsNone(self.subject.is_opening)
        self.dps[COMMAND_DPS] = "close"
        self.assertIsNone(self.subject.is_opening)
        self.dps[COMMAND_DPS] = "stop"
        self.assertIsNone(self.subject.is_opening)

    def test_is_closing(self):
        self.dps[COMMAND_DPS] = "close"
        self.dps[POSITION_DPS] = 100
        self.assertFalse(self.subject.is_closing)
        self.dps[POSITION_DPS] = 50
        self.assertIsNone(self.subject.is_closing)
        self.dps[COMMAND_DPS] = "open"
        self.assertIsNone(self.subject.is_closing)
        self.dps[COMMAND_DPS] = "stop"
        self.assertIsNone(self.subject.is_closing)

    def test_is_closed(self):
        self.dps[COMMAND_DPS] = "close"
        self.dps[POSITION_DPS] = 0
        self.assertFalse(self.subject.is_closed)
        self.dps[POSITION_DPS] = 100
        self.assertTrue(self.subject.is_closed)
        self.dps[COMMAND_DPS] = "stop"
        self.assertTrue(self.subject.is_closed)

    async def test_open_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "open"},
        ):
            await self.subject.async_open_cover()

    async def test_close_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "close"},
        ):
            await self.subject.async_close_cover()

    async def test_stop_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "stop"},
        ):
            await self.subject.async_stop_cover()

    async def test_set_cover_position(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POSITION_DPS: 23},
        ):
            await self.subject.async_set_cover_position(77)

    def test_extra_state_attributes(self):
        self.dps[BACKMODE_DPS] = False
        self.dps[ACTION_DPS] = "test2"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "control_back_mode": False,
                "work_state": "test2",
            },
        )
