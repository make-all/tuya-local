"""Tests for the M027 curtain module."""
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.const import UnitOfTime

from ..const import M027_CURTAIN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DPS = "1"
POSITION_DPS = "2"
CURRENTPOS_DPS = "3"
MODE_DPS = "4"
ACTION_DPS = "7"
TIMER_DPS = "9"
TRAVELTIME_DPS = "10"
UNKNOWN12_DPS = "12"
UNKNOWN101_DPS = "101"


class TestM027Curtains(MultiSensorTests, BasicSelectTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("m027_curtain.yaml", M027_CURTAIN_PAYLOAD)
        self.subject = self.entities["cover_curtain"]
        self.setUpMultiSensors(
            [
                {
                    "dps": TRAVELTIME_DPS,
                    "name": "sensor_travel_time",
                    "min": 1,
                    "max": 120000,
                    "unit": UnitOfTime.MILLISECONDS,
                },
                {
                    "dps": TIMER_DPS,
                    "name": "sensor_time_remaining",
                    "min": 0,
                    "max": 86400,
                    "unit": UnitOfTime.SECONDS,
                },
            ]
        )
        self.setUpBasicSelect(
            MODE_DPS,
            self.entities.get("select_mode"),
            {
                "morning": "Morning",
                "night": "Night",
            },
        ),
        self.mark_secondary(
            [
                "binary_sensor_fault",
                "select_mode",
                "sensor_time_remaining",
                "sensor_travel_time",
            ]
        )

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
        self.dps[CURRENTPOS_DPS] = 47
        self.assertEqual(self.subject.current_cover_position, 47)

    def test_is_opening(self):
        self.dps[ACTION_DPS] = "opening"
        self.dps[CURRENTPOS_DPS] = 100
        self.assertFalse(self.subject.is_opening)
        self.dps[CURRENTPOS_DPS] = 50
        self.assertTrue(self.subject.is_opening)
        self.dps[ACTION_DPS] = "closing"
        self.assertFalse(self.subject.is_opening)
        self.dps[ACTION_DPS] = "opening"
        self.dps[CURRENTPOS_DPS] = None
        self.assertFalse(self.subject.is_opening)

    def test_is_closing(self):
        self.dps[ACTION_DPS] = "closing"
        self.dps[CURRENTPOS_DPS] = 0
        self.assertFalse(self.subject.is_closing)
        self.dps[CURRENTPOS_DPS] = 50
        self.assertTrue(self.subject.is_closing)
        self.dps[ACTION_DPS] = "opening"
        self.assertFalse(self.subject.is_closing)
        self.dps[ACTION_DPS] = "closing"
        self.dps[CURRENTPOS_DPS] = None
        self.assertFalse(self.subject.is_closing)

    def test_is_closed(self):
        self.dps[CURRENTPOS_DPS] = 100
        self.assertFalse(self.subject.is_closed)
        self.dps[CURRENTPOS_DPS] = 0
        self.assertTrue(self.subject.is_closed)
        self.dps[ACTION_DPS] = "closing"
        self.dps[CURRENTPOS_DPS] = None
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
            await self.subject.async_set_cover_position(23)
