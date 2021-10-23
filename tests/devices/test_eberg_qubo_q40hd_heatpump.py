from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE, TEMP_CELSIUS, TEMP_FAHRENHEIT

from ..const import EBERG_QUBO_Q40HD_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
FAN_DPS = "5"
UNIT_DPS = "19"
TIMER_DPS = "22"
UNKNOWN25_DPS = "25"
UNKNOWN30_DPS = "30"
UNKNOWN101_DPS = "101"


class TestEbergQuboQ40HDHeatpump(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "eberg_qubo_q40hd_heatpump.yaml",
            EBERG_QUBO_Q40HD_PAYLOAD,
        )
        self.subject = self.entities.get("climate")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE,
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "wet"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "wind"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.min_temp, 15)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.min_temp, 60)

    def test_maximum_target_temperature(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.max_temp, 30)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.max_temp, 86)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 24}
        ):
            await self.subject.async_set_temperature(temperature=24)

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called()

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25},
        ):
            await self.subject.async_set_target_temperature(25)

        self.dps[UNIT_DPS] = "f"
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 70},
        ):
            await self.subject.async_set_target_temperature(70)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 23}
        ):
            await self.subject.async_set_target_temperature(22.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(14\\) must be between 15 and 30"
        ):
            await self.subject.async_set_target_temperature(14)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(31\\) must be between 15 and 30"
        ):
            await self.subject.async_set_target_temperature(31)

        self.dps[UNIT_DPS] = "f"
        with self.assertRaisesRegex(
            ValueError, "temperature \\(59\\) must be between 60 and 86"
        ):
            await self.subject.async_set_target_temperature(59)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(87\\) must be between 60 and 86"
        ):
            await self.subject.async_set_target_temperature(87)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)

        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = "wet"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_DRY)

        self.dps[HVACMODE_DPS] = "wind"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

        self.dps[HVACMODE_DPS] = "wind"
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_OFF,
                HVAC_MODE_COOL,
                HVAC_MODE_DRY,
                HVAC_MODE_FAN_ONLY,
                HVAC_MODE_HEAT,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "cold"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_COOL)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_fan_mode(self):
        self.dps[HVACMODE_DPS] = "cold"
        self.dps[FAN_DPS] = "low"
        self.assertEqual(self.subject.fan_mode, "low")
        self.dps[FAN_DPS] = "middle"
        self.assertEqual(self.subject.fan_mode, "medium")
        self.dps[FAN_DPS] = "high"
        self.assertEqual(self.subject.fan_mode, "high")
        self.dps[FAN_DPS] = "auto"
        self.assertEqual(self.subject.fan_mode, "auto")

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            [
                "auto",
                "low",
                "medium",
                "high",
            ],
        )

    async def test_set_fan_mode_to_low(self):
        self.dps[HVACMODE_DPS] = "cold"
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "low"},
        ):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_mode_to_low_fails_when_heating(self):
        self.dps[HVACMODE_DPS] = "hot"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_mode_to_medium(self):
        self.dps[HVACMODE_DPS] = "cold"
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "middle"},
        ):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_mode_to_medium_fails_when_heating_or_drying(self):
        self.dps[HVACMODE_DPS] = "hot"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("medium")

        self.dps[HVACMODE_DPS] = "wet"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_mode_to_high(self):
        self.dps[HVACMODE_DPS] = "cold"
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "high"},
        ):
            await self.subject.async_set_fan_mode("high")

    async def test_set_fan_mode_to_high_fails_when_drying(self):
        self.dps[HVACMODE_DPS] = "wet"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("high")

    async def test_set_fan_mode_to_auto(self):
        self.dps[HVACMODE_DPS] = "cold"
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "auto"},
        ):
            await self.subject.async_set_fan_mode("auto")

    async def test_set_fan_mode_to_auto_fails_unless_cooling(self):
        self.dps[HVACMODE_DPS] = "hot"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("auto")

        self.dps[HVACMODE_DPS] = "wet"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("auto")

        self.dps[HVACMODE_DPS] = "wind"
        with self.assertRaises(AttributeError):
            await self.subject.async_set_fan_mode("auto")

    def test_device_state_attribures(self):
        self.dps[TIMER_DPS] = 22
        self.dps[UNKNOWN25_DPS] = True
        self.dps[UNKNOWN30_DPS] = False
        self.dps[UNKNOWN101_DPS] = "101"
        self.assertDictEqual(
            self.subject.device_state_attributes,
            {
                "timer": 22,
                "unknown_25": True,
                "unknown_30": False,
                "unknown_101": "101",
            },
        )
