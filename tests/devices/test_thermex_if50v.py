from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_ELECTRIC,
    STATE_OFF,
    STATE_PERFORMANCE,
    WaterHeaterEntityFeature,
)
from homeassistant.const import PRECISION_WHOLE, UnitOfTemperature

from ..const import THERMEX_IF50V_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DP = "101"
TEMPERATURE_DP = "104"
CURRENTTEMP_DP = "102"
MODE_DP = "105"
ERROR_DP = "106"


class TestThermexIF50V(
    BasicBinarySensorTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "thermex_if50v_waterheater.yaml",
            THERMEX_IF50V_PAYLOAD,
        )
        self.subject = self.entities.get("water_heater")
        self.setUpBasicBinarySensor(
            ERROR_DP,
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["binary_sensor_problem"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            WaterHeaterEntityFeature.OPERATION_MODE
            | WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.AWAY_MODE,
        )

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_precision(self):
        self.assertEqual(self.subject.precision, PRECISION_WHOLE)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DP] = 55
        self.assertEqual(self.subject.current_temperature, 55)

    def test_min_temp(self):
        self.assertEqual(self.subject.min_temp, 15)

    def test_max_temp(self):
        self.assertEqual(self.subject.max_temp, 75)

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DP] = 61
        self.assertEqual(self.subject.target_temperature, 61)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_operation_list(self):
        self.assertCountEqual(
            self.subject.operation_list,
            [
                STATE_ECO,
                STATE_ELECTRIC,
                STATE_PERFORMANCE,
                STATE_OFF,
                "away",
            ],
        )

    def test_current_operation(self):
        self.dps[POWER_DP] = True
        self.dps[MODE_DP] = "3"
        self.assertEqual(self.subject.current_operation, STATE_ECO)
        self.dps[MODE_DP] = "1"
        self.assertEqual(self.subject.current_operation, STATE_PERFORMANCE)
        self.dps[MODE_DP] = "2"
        self.assertEqual(self.subject.current_operation, STATE_ELECTRIC)
        self.dps[MODE_DP] = "4"
        self.assertEqual(self.subject.current_operation, "away")
        self.dps[POWER_DP] = False
        self.assertEqual(self.subject.current_operation, STATE_OFF)

    def test_is_away_mode_redirects_to_mode(self):
        self.dps[POWER_DP] = True
        self.dps[MODE_DP] = "4"
        self.assertTrue(self.subject.is_away_mode_on)
        self.dps[MODE_DP] = "2"
        self.assertFalse(self.subject.is_away_mode_on)

    async def test_set_temperature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DP: 65},
        ):
            await self.subject.async_set_temperature(temperature=65)

    async def test_set_operation_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True, MODE_DP: "3"},
        ):
            await self.subject.async_set_operation_mode(STATE_ECO)

    async def test_set_operation_mode_with_temperature_service(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True, MODE_DP: "3"},
        ):
            await self.subject.async_set_temperature(operation_mode=STATE_ECO)

    async def test_set_operation_mode_to_electric(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True, MODE_DP: "2"},
        ):
            await self.subject.async_set_operation_mode(STATE_ELECTRIC)

    async def test_set_operation_mode_to_performance(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True, MODE_DP: "1"},
        ):
            await self.subject.async_set_operation_mode(STATE_PERFORMANCE)

    async def test_set_operation_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: False},
        ):
            await self.subject.async_set_operation_mode(STATE_OFF)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True},
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: False},
        ):
            await self.subject.async_turn_off()

    async def test_turn_away_mode_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True, MODE_DP: "4"},
        ):
            await self.subject.async_turn_away_mode_on()

    async def test_turn_away_mode_off(self):
        self.dps[POWER_DP] = True
        self.dps[MODE_DP] = "4"

        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DP: True, MODE_DP: "2"},
        ):
            await self.subject.async_turn_away_mode_off()
