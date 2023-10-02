"""Tests for the simple garage door opener."""
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature

from ..const import SIMPLE_GARAGE_DOOR_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
OPEN_DPS = "101"


class TestSimpleGarageOpener(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("garage_door_opener.yaml", SIMPLE_GARAGE_DOOR_PAYLOAD)
        self.subject = self.entities["cover_garage"]

    def test_device_class_is_garage(self):
        self.assertEqual(self.subject.device_class, CoverDeviceClass.GARAGE)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE,
        )

    def test_current_cover_position(self):
        self.dps[OPEN_DPS] = True
        self.assertEqual(self.subject.current_cover_position, 100)
        self.dps[OPEN_DPS] = False
        self.assertEqual(self.subject.current_cover_position, 0)

    def test_is_opening(self):
        self.dps[SWITCH_DPS] = False
        self.dps[OPEN_DPS] = False
        self.assertFalse(self.subject.is_opening)
        self.dps[OPEN_DPS] = True
        self.assertFalse(self.subject.is_opening)
        self.dps[SWITCH_DPS] = True
        self.assertFalse(self.subject.is_opening)
        self.dps[OPEN_DPS] = False
        self.assertTrue(self.subject.is_opening)

    def test_is_closing(self):
        self.dps[SWITCH_DPS] = False
        self.dps[OPEN_DPS] = False
        self.assertFalse(self.subject.is_closing)
        self.dps[OPEN_DPS] = True
        self.assertTrue(self.subject.is_closing)
        self.dps[SWITCH_DPS] = True
        self.assertFalse(self.subject.is_closing)
        self.dps[OPEN_DPS] = False
        self.assertFalse(self.subject.is_closing)

    def test_is_closed(self):
        self.dps[SWITCH_DPS] = False
        self.dps[OPEN_DPS] = True
        self.assertFalse(self.subject.is_closed)
        self.dps[OPEN_DPS] = False
        self.assertTrue(self.subject.is_closed)

    async def test_open_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True},
        ):
            await self.subject.async_open_cover()

    async def test_close_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: False},
        ):
            await self.subject.async_close_cover()

    async def test_set_cover_position_not_supported(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_set_cover_position(50)

    async def test_stop_cover_not_supported(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_stop_cover()

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})
