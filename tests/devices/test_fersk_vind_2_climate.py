from homeassistant.components.climate.const import (
    SWING_OFF,
    SWING_VERTICAL,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature

from ..const import FERSK_VIND2_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
FAN_DPS = "5"
UNIT_DPS = "19"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"
TIMER_DPS = "103"
SWING_DPS = "104"
COUNTDOWN_DPS = "105"
UNKNOWN106_DPS = "106"
UNKNOWN109_DPS = "109"
UNKNOWN110_DPS = "110"


class TestFerskVind2Climate(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("fersk_vind_2_climate.yaml", FERSK_VIND2_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16,
            max=32,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.SWING_MODE
            ),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "COOL"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "FAN"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[HVACMODE_DPS] = "DRY"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "HEAT"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

    def test_minimum_target_temperature_f(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.min_temp, 60)

    def test_maximum_target_temperature_f(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.max_temp, 90)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "COOL"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[HVACMODE_DPS] = "FAN"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)
        self.dps[HVACMODE_DPS] = "DRY"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)
        self.dps[HVACMODE_DPS] = "HEAT"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
                HVACMode.HEAT,
                HVACMode.OFF,
            ],
        )

    async def test_set_hvac_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    async def test_set_hvac_mode_cool(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "COOL"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_dry(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "DRY"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.DRY)

    async def test_set_hvac_mode_fan(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "FAN"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.FAN_ONLY)

    async def test_set_hvac_mode_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "HEAT"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = 1
        self.assertEqual(self.subject.fan_mode, "low")
        self.dps[FAN_DPS] = 2
        self.assertEqual(self.subject.fan_mode, "medium")
        self.dps[FAN_DPS] = 3
        self.assertEqual(self.subject.fan_mode, "high")

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            ["low", "medium", "high"],
        )

    async def test_set_fan_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 1},
        ):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 2},
        ):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 3},
        ):
            await self.subject.async_set_fan_mode("high")

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            [SWING_OFF, SWING_VERTICAL],
        )

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)
        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, SWING_VERTICAL)

    async def test_set_swing_mode_to_vertical(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode(SWING_VERTICAL)

    async def test_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode(SWING_OFF)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN101_DPS] = True
        self.dps[UNKNOWN102_DPS] = False
        self.dps[TIMER_DPS] = 103
        self.dps[COUNTDOWN_DPS] = 105
        self.dps[UNKNOWN106_DPS] = 106
        self.dps[UNKNOWN109_DPS] = True
        self.dps[UNKNOWN110_DPS] = 110
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_101": True,
                "unknown_102": False,
                "timer": 103,
                "countdown": 105,
                "unknown_106": 106,
                "unknown_109": True,
                "unknown_110": 110,
            },
        )
