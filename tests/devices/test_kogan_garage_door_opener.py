"""Tests for the simple garage door opener."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from homeassistant.components.sensor import SensorDeviceClass

from ..const import KOGAN_GARAGE_DOOR_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

CONTROL_DPS = "101"
ACTION_DPS = "102"
BATTERY_DPS = "104"
LEFTOPEN_DPS = "105"


class TestKoganGarageOpener(
    BasicBinarySensorTests,
    BasicSensorTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("kogan_garage_opener.yaml", KOGAN_GARAGE_DOOR_PAYLOAD)
        self.subject = self.entities["cover_garage"]
        self.setUpBasicBinarySensor(
            LEFTOPEN_DPS,
            self.entities.get("binary_sensor_door_open"),
            device_class=BinarySensorDeviceClass.GARAGE_DOOR,
        )
        self.setUpBasicSensor(
            BATTERY_DPS,
            self.entities.get("sensor_battery"),
            device_class=SensorDeviceClass.BATTERY,
        )
        self.mark_secondary(["binary_sensor_door_open", "sensor_battery"])

    def test_device_class_is_garage(self):
        self.assertEqual(self.subject.device_class, CoverDeviceClass.GARAGE)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE,
        )

    def test_current_cover_position(self):
        self.dps[ACTION_DPS] = "opened"
        self.dps[CONTROL_DPS] = "fopen"
        self.assertEqual(self.subject.current_cover_position, 100)
        self.dps[ACTION_DPS] = "closed"
        self.dps[CONTROL_DPS] = "fclose"
        self.assertEqual(self.subject.current_cover_position, 0)
        self.dps[ACTION_DPS] = "closing"
        self.assertEqual(self.subject.current_cover_position, 50)

    def test_is_opening(self):
        self.dps[ACTION_DPS] = "opened"
        self.assertFalse(self.subject.is_opening)
        self.dps[ACTION_DPS] = "closed"
        self.assertFalse(self.subject.is_opening)
        self.dps[ACTION_DPS] = "closing"
        self.assertFalse(self.subject.is_opening)
        self.dps[ACTION_DPS] = "openning"
        self.assertTrue(self.subject.is_opening)

    def test_is_closing(self):
        self.dps[ACTION_DPS] = "opened"
        self.assertFalse(self.subject.is_closing)
        self.dps[ACTION_DPS] = "closed"
        self.assertFalse(self.subject.is_closing)
        self.dps[ACTION_DPS] = "openning"
        self.assertFalse(self.subject.is_closing)
        self.dps[ACTION_DPS] = "closing"
        self.assertTrue(self.subject.is_closing)

    def test_is_closed(self):
        self.dps[CONTROL_DPS] = "fclose"
        self.dps[ACTION_DPS] = "closing"
        self.assertFalse(self.subject.is_closed)
        self.dps[ACTION_DPS] = "closed"
        self.assertTrue(self.subject.is_closed)

    async def test_open_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {CONTROL_DPS: "fopen"},
        ):
            await self.subject.async_open_cover()

    async def test_close_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {CONTROL_DPS: "fclose"},
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
