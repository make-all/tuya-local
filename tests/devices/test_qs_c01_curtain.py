"""Tests for the QS C01 curtain module."""
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.const import UnitOfTime

from ..const import QS_C01_CURTAIN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import BasicNumberTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DPS = "1"
POSITION_DPS = "2"
BACKMODE_DPS = "8"
TRAVELTIME_DPS = "10"


class TestQSC01Curtains(BasicNumberTests, BasicSelectTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("qs_c01_curtain.yaml", QS_C01_CURTAIN_PAYLOAD)
        self.subject = self.entities["cover_curtain"]
        self.setUpBasicNumber(
            TRAVELTIME_DPS,
            self.entities.get("number_travel_time"),
            min=1,
            max=60,
            unit=UnitOfTime.SECONDS,
        )
        self.setUpBasicSelect(
            BACKMODE_DPS,
            self.entities.get("select_motor_reverse_mode"),
            {
                "forward": "Forward",
                "back": "Back",
            },
        ),
        self.mark_secondary(["number_travel_time", "select_motor_reverse_mode"])

    def test_device_class_is_curtain(self):
        self.assertEqual(self.subject.device_class, CoverDeviceClass.CURTAIN)

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
        self.assertEqual(self.subject.current_cover_position, 47)

    def test_is_opening(self):
        self.dps[COMMAND_DPS] = "open"
        self.dps[POSITION_DPS] = 100
        self.assertFalse(self.subject.is_opening)
        self.dps[POSITION_DPS] = 50
        self.assertTrue(self.subject.is_opening)
        self.dps[COMMAND_DPS] = "close"
        self.assertFalse(self.subject.is_opening)
        self.dps[COMMAND_DPS] = "stop"
        self.assertFalse(self.subject.is_opening)

    def test_is_closing(self):
        self.dps[COMMAND_DPS] = "close"
        self.dps[POSITION_DPS] = 0
        self.assertFalse(self.subject.is_closing)
        self.dps[POSITION_DPS] = 50
        self.assertTrue(self.subject.is_closing)
        self.dps[COMMAND_DPS] = "open"
        self.assertFalse(self.subject.is_closing)
        self.dps[COMMAND_DPS] = "stop"
        self.assertFalse(self.subject.is_closing)

    def test_is_closed(self):
        self.dps[COMMAND_DPS] = "close"
        self.dps[POSITION_DPS] = 100
        self.assertFalse(self.subject.is_closed)
        self.dps[POSITION_DPS] = 0
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
            {POSITION_DPS: 20},
        ):
            # step is 10, so expect rounding to 20
            await self.subject.async_set_cover_position(23)
