from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from ..const import HELLNAR_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"


class TestHellnarHeatpump(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("hellnar_heatpump.yaml", HELLNAR_HEATPUMP_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=17.0,
            max=30.0,
            scale=10,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (ClimateEntityFeature.SWING_MODE | ClimateEntityFeature.TARGET_TEMPERATURE),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:hvac")
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

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_minimum_target_temperature_in_hot(self):
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.min_temp, 0.0)

    def test_maximum_target_temperature_in_hot(self):
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.max_temp, 30.0)

    async def test_set_target_temperature_fails_outside_valid_range_in_hot(self):
        self.dps[HVACMODE_DPS] = "hot"
        with self.assertRaisesRegex(
            ValueError, "temperature \\(31\\) must be between 0.0 and 30.0"
        ):
            await self.subject.async_set_target_temperature(31)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

        self.dps[HVACMODE_DPS] = "wet"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)

        self.dps[HVACMODE_DPS] = "wind"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)

        self.dps[HVACMODE_DPS] = "auto"
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
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "hot"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_extra_state_attributes(self):
        self.dps["5"] = "fan?"
        self.dps["18"] = 18
        self.dps["20"] = 20
        self.dps["105"] = "unknown105"
        self.dps["110"] = 110
        self.dps["113"] = "unknown113"
        self.dps["114"] = "unknown114"
        self.dps["119"] = "unknown119"
        self.dps["120"] = "unknown120"
        self.dps["126"] = "unknown126"
        self.dps["127"] = "unknown127"
        self.dps["128"] = "unknown128"
        self.dps["129"] = "unknown129"
        self.dps["130"] = 130
        self.dps["131"] = True
        self.dps["132"] = False
        self.dps["133"] = "unknown133"
        self.dps["134"] = "unknown134"

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "maybe_fan_mode": "fan?",
                "unknown_18": 18,
                "unknown_20": 20,
                "unknown_105": "unknown105",
                "unknown_110": 110,
                "unknown_113": "unknown113",
                "unknown_114": "unknown114",
                "unknown_119": "unknown119",
                "unknown_120": "unknown120",
                "unknown_126": "unknown126",
                "unknown_127": "unknown127",
                "unknown_128": "unknown128",
                "unknown_129": "unknown129",
                "maybe_eco_temp": 130,
                "unknown_131": True,
                "unknown_132": False,
                "unknown_133": "unknown133",
                "unknown_134": "unknown134",
            },
        )
