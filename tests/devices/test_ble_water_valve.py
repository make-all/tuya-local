"""Tests for the BLE water valve."""

from homeassistant.components.valve import ValveDeviceClass, ValveEntityFeature

from ..const import BLE_WATERVALVE_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

VALVE_DP = "1"
PROBLEM_DP = "4"
BATTERY_DP = "7"
TOTALUSE_DP = "9"
WEATHERDELAY_DP = "10"
IRRIGTIME = "11"
OPERATION_DP = "12"
WEATHER_DP = "13"
WEATHERSW_DP = "14"
LASTUSE_DP = "15"
SOAKSCHED_DP = "16"
IRRIGSCHED_DP = "17"


class TestBLEValve(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("ble_water_valve.yaml", BLE_WATERVALVE_PAYLOAD)
        self.subject = self.entities["valve_water"]
        self.mark_secondary(
            [
                "switch",
                "sensor_battery",
                "binary_sensor_problem",
                "sensor_operation",
                "sensor_accumulated_use_time",
                "sensor_last_use_time",
                "select_weather_delay",
                "number_irrigation_time",
                "time_irrigation_time",
                "switch_smart_weather_switch",
            ]
        )

    def test_device_class_is_water(self):
        self.assertEqual(self.subject.device_class, ValveDeviceClass.WATER)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE,
        )

    def test_is_closed(self):
        self.dps[VALVE_DP] = True
        self.assertFalse(self.subject.is_closed)
        self.dps[VALVE_DP] = False
        self.assertTrue(self.subject.is_closed)

    async def test_open_valve(self):
        async with assert_device_properties_set(
            self.subject._device,
            {VALVE_DP: True},
        ):
            await self.subject.async_open_valve()

    async def test_close_valve(self):
        async with assert_device_properties_set(
            self.subject._device,
            {VALVE_DP: False},
        ):
            await self.subject.async_close_valve()

    def test_extra_state_attributes(self):
        self.dps[WEATHER_DP] = "Sunny"
        self.dps[SOAKSCHED_DP] = "soaktest"
        self.dps[IRRIGSCHED_DP] = "irrigationtest"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "weather": "Sunny",
                "soak_schedule": "soaktest",
                "irrigation_schedule": "irrigationtest",
            },
        )
