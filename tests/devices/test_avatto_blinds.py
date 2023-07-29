"""Tests for the Avatto roller blinds controller."""
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTime

from ..const import AVATTO_BLINDS_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DP = "1"
POSITION_DP = "2"
CURRENTPOS_DP = "3"
BACK_DP = "5"
ACTION_DP = "7"
TIMER_DP = "8"
COUNTDOWN_DP = "9"
TRAVELTIME_DP = "11"


class TestAvattoBlinds(MultiSensorTests, BasicSelectTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("avatto_roller_blinds.yaml", AVATTO_BLINDS_PAYLOAD)
        self.subject = self.entities["cover_blind"]
        self.setUpMultiSensors(
            [
                {
                    "dps": TRAVELTIME_DP,
                    "name": "sensor_travel_time",
                    "min": 0,
                    "max": 120000,
                    "unit": UnitOfTime.MILLISECONDS,
                },
                {
                    "dps": COUNTDOWN_DP,
                    "name": "sensor_timer",
                    "device_class": SensorDeviceClass.DURATION,
                    "min": 0,
                    "max": 86400,
                    "unit": UnitOfTime.SECONDS,
                },
            ]
        )
        self.setUpBasicSelect(
            TIMER_DP,
            self.entities.get("select_timer"),
            {
                "cancel": "Off",
                "1": "1 hour",
                "2": "2 hours",
                "3": "3 hours",
                "4": "4 hours",
            },
        ),
        self.mark_secondary(["sensor_travel_time", "sensor_timer", "select_timer"])

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
        self.dps[CURRENTPOS_DP] = 47
        self.assertEqual(self.subject.current_cover_position, 47)

    def test_is_opening(self):
        self.dps[ACTION_DP] = "opening"
        self.dps[CURRENTPOS_DP] = 100
        self.assertFalse(self.subject.is_opening)
        self.dps[CURRENTPOS_DP] = 50
        self.assertTrue(self.subject.is_opening)
        self.dps[ACTION_DP] = "closing"
        self.assertFalse(self.subject.is_opening)
        self.dps[ACTION_DP] = "opening"
        self.dps[CURRENTPOS_DP] = None
        self.assertFalse(self.subject.is_opening)

    def test_is_closing(self):
        self.dps[ACTION_DP] = "closing"
        self.dps[CURRENTPOS_DP] = 0
        self.assertFalse(self.subject.is_closing)
        self.dps[CURRENTPOS_DP] = 50
        self.assertTrue(self.subject.is_closing)
        self.dps[ACTION_DP] = "opening"
        self.assertFalse(self.subject.is_closing)
        self.dps[ACTION_DP] = "closing"
        self.dps[CURRENTPOS_DP] = None
        self.assertFalse(self.subject.is_closing)

    def test_is_closed(self):
        self.dps[CURRENTPOS_DP] = 100
        self.assertFalse(self.subject.is_closed)
        self.dps[CURRENTPOS_DP] = 0
        self.assertTrue(self.subject.is_closed)
        self.dps[ACTION_DP] = "closing"
        self.dps[CURRENTPOS_DP] = None
        self.assertTrue(self.subject.is_closed)

    async def test_open_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "open"},
        ):
            await self.subject.async_open_cover()

    async def test_close_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "close"},
        ):
            await self.subject.async_close_cover()

    async def test_stop_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "stop"},
        ):
            await self.subject.async_stop_cover()

    async def test_set_cover_position(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POSITION_DP: 23},
        ):
            await self.subject.async_set_cover_position(23)
