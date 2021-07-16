from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import HELLNAR_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"


class TestHellnarHeatpump(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("hellnar_heatpump.yaml", HELLNAR_HEATPUMP_PAYLOAD)
        self.subject = self.entities.get("climate")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_SWING_MODE | SUPPORT_TARGET_TEMPERATURE,
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

    def test_target_temperature(self):
        self.dps[HVACMODE_DPS] = "auto"
        self.dps[TEMPERATURE_DPS] = 250
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 0.1)

    def test_minimum_target_temperature(self):
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.min_temp, 170)
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.min_temp, 0)

    def test_maximum_target_temperature(self):
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.max_temp, 300)
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.max_temp, 300)

    async def test_legacy_set_temperature_with_temperature(self):
        self.dps[HVACMODE_DPS] = "auto"
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 240}
        ):
            await self.subject.async_set_temperature(temperature=24)

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        self.dps[HVACMODE_DPS] = "auto"
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        self.dps[HVACMODE_DPS] = "auto"
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 250},
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        self.dps[HVACMODE_DPS] = "cold"
        with self.assertRaisesRegex(
            ValueError, "temperature \\(150\\) must be between 170 and 300"
        ):
            await self.subject.async_set_target_temperature(15)

        self.dps[HVACMODE_DPS] = "hot"
        with self.assertRaisesRegex(
            ValueError, "temperature \\(330\\) must be between 0 and 300"
        ):
            await self.subject.async_set_target_temperature(33)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)

        self.dps[HVACMODE_DPS] = "wet"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_DRY)

        self.dps[HVACMODE_DPS] = "wind"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_AUTO)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

        self.dps[HVACMODE_DPS] = "auto"
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_OFF,
                HVAC_MODE_HEAT,
                HVAC_MODE_AUTO,
                HVAC_MODE_COOL,
                HVAC_MODE_DRY,
                HVAC_MODE_FAN_ONLY,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "hot"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_device_state_attributes(self):
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

        self.assertCountEqual(
            self.subject.device_state_attributes,
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
