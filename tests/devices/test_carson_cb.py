from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE, TEMP_CELSIUS, TEMP_FAHRENHEIT

from ..const import CARSON_CB_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
FAN_DPS = "5"
UNIT_DPS = "19"
UNKNOWN102_DPS = "102"
TIMER_DPS = "103"
SWING_DPS = "104"
COUNTDOWN_DPS = "105"
UNKNOWN106_DPS = "106"
UNKNOWN110_DPS = "110"


class TestCarsonCBHeatpump(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("carson_cb.yaml", CARSON_CB_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16,
            max=30,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE,
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "COOL"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "HEAT"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "DRY"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "FAN"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "HEAT"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = "COOL"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)

        self.dps[HVACMODE_DPS] = "DRY"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_DRY)

        self.dps[HVACMODE_DPS] = "FAN"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

        self.dps[HVACMODE_DPS] = "DRY"
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_OFF,
                HVAC_MODE_HEAT,
                HVAC_MODE_COOL,
                HVAC_MODE_DRY,
                HVAC_MODE_FAN_ONLY,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "HEAT"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

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
            [
                "low",
                "medium",
                "high",
            ],
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
            ["off", "vertical"],
        )

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, "off")

        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, "vertical")

    async def test_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode("off")

    async def test_set_swing_mode_to_vertical(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode("vertical")

    def test_extra_state_attribures(self):
        self.dps[UNKNOWN102_DPS] = True
        self.dps[TIMER_DPS] = 103
        self.dps[COUNTDOWN_DPS] = 105
        self.dps[UNKNOWN106_DPS] = 106
        self.dps[UNKNOWN110_DPS] = 110
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_102": True,
                "timer": 103,
                "countdown": 105,
                "unknown_106": 106,
                "unknown_110": 110,
            },
        )
