"""Tests for the Quto 03 Sprinkler."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.valve import ValveDeviceClass, ValveEntityFeature
from homeassistant.const import UnitOfTime

from ..const import QOTO_SPRINKLER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.number import MultiNumberTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

TARGET_DPS = "102"
CURRENT_DPS = "103"
COUNTDOWN_DPS = "104"
TIMER_DPS = "105"
ERROR_DPS = "108"


class TestQotoSprinkler(
    BasicBinarySensorTests,
    MultiNumberTests,
    MultiSensorTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("qoto_03_sprinkler.yaml", QOTO_SPRINKLER_PAYLOAD)
        self.subject = self.entities.get("valve_water")
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpMultiNumber(
            [
                {
                    "name": "number_timer",
                    "dps": TIMER_DPS,
                    "max": 86399,
                    "device_class": NumberDeviceClass.DURATION,
                    "unit": UnitOfTime.SECONDS,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_open",
                    "dps": CURRENT_DPS,
                    "unit": "%",
                },
                {
                    "name": "sensor_time_remaining",
                    "dps": COUNTDOWN_DPS,
                    "device_class": "duration",
                    "unit": "s",
                },
            ]
        )
        self.mark_secondary(
            [
                "number",
                "binary_sensor_problem",
                "number_timer",
                "sensor_open",
                "sensor_time_remaining",
                "time_timer",
            ]
        )

    def test_device_class_is_water(self):
        self.assertEqual(self.subject.device_class, ValveDeviceClass.WATER)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ValveEntityFeature.OPEN
            | ValveEntityFeature.CLOSE
            | ValveEntityFeature.SET_POSITION,
        )

    def test_is_closed(self):
        self.dps[TARGET_DPS] = 100
        self.assertFalse(self.subject.is_closed)
        self.dps[TARGET_DPS] = 50
        self.assertFalse(self.subject.is_closed)
        self.dps[TARGET_DPS] = 0
        self.assertTrue(self.subject.is_closed)

    def test_current_position(self):
        self.dps[TARGET_DPS] = 100
        self.assertEqual(self.subject.current_position, 100)
        self.dps[TARGET_DPS] = 50
        self.assertEqual(self.subject.current_position, 50)
        self.dps[TARGET_DPS] = 0
        self.assertEqual(self.subject.current_position, 0)

    async def test_open_valve(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TARGET_DPS: 100},
        ):
            await self.subject.async_open_valve()

    async def test_close_valve(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TARGET_DPS: 0},
        ):
            await self.subject.async_close_valve()

    async def test_set_valve_position(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TARGET_DPS: 50},
        ):
            await self.subject.async_set_valve_position(50)

    def test_basic_bsensor_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 2
        self.assertDictEqual(
            self.basicBSensor.extra_state_attributes,
            {"fault_code": 2},
        )
