from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.const import (
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from ..const import EBERG_COOLY_C35HD_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
UNKNOWN4_DPS = "4"
HVACMODE_DPS = "5"
TEMPERATURE_DPS = "6"
FAN_DPS = "8"
UNIT_DPS = "10"
UNKNOWN13_DPS = "13"
UNKNOWN14_DPS = "14"
UNKNOWN15_DPS = "15"
SWING_DPS = "16"
UNKNOWN17_DPS = "17"
TEMPF_DPS = "18"
UNKNOWN19_DPS = "19"


class TestEbergCoolyC35HDHeatpump(
    BasicSelectTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "eberg_cooly_c35hd.yaml",
            EBERG_COOLY_C35HD_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=13,
            max=32,
        )
        self.setUpBasicSelect(
            UNIT_DPS,
            self.entities.get("select_temperature_unit"),
            {
                True: "Fahrenheit",
                False: "Celsius",
            },
        )
        self.mark_secondary(["select_temperature_unit"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "3"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "4"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = False
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)
        self.dps[UNIT_DPS] = True
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_minimum_target_temperature_f(self):
        self.dps[UNIT_DPS] = True
        self.assertEqual(self.subject.min_temp, 55)

    def test_maximum_target_temperature_f(self):
        self.dps[UNIT_DPS] = True
        self.assertEqual(self.subject.max_temp, 90)

    def test_temperature_redirects_f(self):
        self.dps[UNIT_DPS] = True
        self.dps[TEMPERATURE_DPS] = 20
        self.dps[TEMPF_DPS] = 90
        self.assertEqual(self.subject.target_temperature, 90)

    async def test_set_temperature_redirects_f(self):
        self.dps[UNIT_DPS] = True
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPF_DPS: 85},
        ):
            await self.subject.async_set_target_temperature(85)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)
        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_DRY)
        self.dps[HVACMODE_DPS] = "3"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)
        self.dps[HVACMODE_DPS] = "4"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

        self.dps[HVACMODE_DPS] = "3"
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

    async def test_set_hvac_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "1"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_set_hvac_mode_to_dry(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "2"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_DRY)

    async def test_set_hvac_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "3"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_COOL)

    async def test_set_hvac_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "4"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "1"
        self.assertEqual(self.subject.fan_mode, "low")
        self.dps[FAN_DPS] = "2"
        self.assertEqual(self.subject.fan_mode, "medium")
        self.dps[FAN_DPS] = "3"
        self.assertEqual(self.subject.fan_mode, "high")
        self.dps[FAN_DPS] = "0"
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
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "1"},
        ):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "2"},
        ):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "3"},
        ):
            await self.subject.async_set_fan_mode("high")

    async def test_set_fan_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "0"},
        ):
            await self.subject.async_set_fan_mode("auto")

    def test_swing_mode(self):
        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, SWING_VERTICAL)
        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            [
                SWING_VERTICAL,
                SWING_OFF,
            ],
        )

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
        self.dps[UNKNOWN4_DPS] = 4
        self.dps[UNKNOWN13_DPS] = 13
        self.dps[UNKNOWN14_DPS] = 14
        self.dps[UNKNOWN15_DPS] = 15
        self.dps[UNKNOWN17_DPS] = True
        self.dps[UNKNOWN19_DPS] = False

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_4": 4,
                "unknown_13": 13,
                "unknown_14": 14,
                "unknown_15": 15,
                "unknown_17": True,
                "unknown_19": False,
            },
        )
