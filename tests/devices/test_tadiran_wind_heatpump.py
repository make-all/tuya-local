from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from ..const import TADIRAN_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
FAN_DPS = "5"


class TestTadiranWindHeatpump(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("tadiran_wind_heatpump.yaml", TADIRAN_HEATPUMP_PAYLOAD)
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
            (ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TARGET_TEMPERATURE),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:hvac")
        self.dps[HVACMODE_DPS] = "cooling"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "heating"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "dehum"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "fan"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 250
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "heating"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "cooling"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

        self.dps[HVACMODE_DPS] = "dehum"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)

        self.dps[HVACMODE_DPS] = "fan"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)

        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "heating"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            ["auto", "low", "medium", "high"],
        )

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "low"
        self.assertEqual(self.subject.fan_mode, "low")
        self.dps[FAN_DPS] = "middle"
        self.assertEqual(self.subject.fan_mode, "medium")
        self.dps[FAN_DPS] = "high"
        self.assertEqual(self.subject.fan_mode, "high")
        self.dps[FAN_DPS] = "auto"
        self.assertEqual(self.subject.fan_mode, "auto")

    async def test_set_fan_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "low"},
        ):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "middle"},
        ):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "high"},
        ):
            await self.subject.async_set_fan_mode("high")

    async def test_set_fan_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "auto"},
        ):
            await self.subject.async_set_fan_mode("auto")

    def test_extra_state_attributes(self):
        self.dps["101"] = 101
        self.dps["102"] = 102
        self.dps["103"] = 103
        self.dps["104"] = "unknown104"
        self.dps["105"] = "unknown105"
        self.dps["106"] = 106
        self.dps["107"] = True
        self.dps["108"] = False

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_101": 101,
                "unknown_102": 102,
                "unknown_103": 103,
                "unknown_104": "unknown104",
                "unknown_105": "unknown105",
                "unknown_106": 106,
                "unknown_107": True,
                "unknown_108": False,
            },
        )
