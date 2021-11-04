from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.light import (
    COLOR_MODE_UNKNOWN,
    SUPPORT_EFFECT,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import KOGAN_KASHMFP20BA_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
PRESET_DPS = "2"
TEMPERATURE_DPS = "3"
CURRENTTEMP_DPS = "4"
BACKLIGHT_DPS = "5"
FLAME_DPS = "6"


class TestKoganKASHMF20BAHeater(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "kogan_kashmfp20ba_heater.yaml", KOGAN_KASHMFP20BA_HEATER_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.backlight = self.entities.get("light_backlight")
        self.flame = self.entities.get("light_flame")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 10)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 30)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 24}
        ):
            await self.subject.async_set_temperature(temperature=24)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "Low"}
        ):
            await self.subject.async_set_temperature(preset_mode="Low")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 26, PRESET_DPS: "High"}
        ):
            await self.subject.async_set_temperature(temperature=26, preset_mode="High")

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called()

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25},
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 23}
        ):
            await self.subject.async_set_target_temperature(22.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(9\\) must be between 10 and 30"
        ):
            await self.subject.async_set_target_temperature(9)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(31\\) must be between 10 and 30"
        ):
            await self.subject.async_set_target_temperature(31)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "low"
        self.assertEqual(self.subject.preset_mode, "low")

        self.dps[PRESET_DPS] = "high"
        self.assertEqual(self.subject.preset_mode, "high")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["low", "high"])

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "low"},
        ):
            await self.subject.async_set_preset_mode("low")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "high"},
        ):
            await self.subject.async_set_preset_mode("high")

    def test_device_state_attribures(self):
        self.assertEqual(self.subject.device_state_attributes, {})
        self.assertEqual(self.backlight.device_state_attributes, {})
        self.assertEqual(self.flame.device_state_attributes, {})

    def test_lighting_supported_color_modes(self):
        self.assertCountEqual(self.backlight.supported_color_modes, [])
        self.assertCountEqual(self.flame.supported_color_modes, [])

    def test_lighting_supported_features(self):
        self.assertEqual(self.backlight.supported_features, SUPPORT_EFFECT)
        self.assertEqual(self.flame.supported_features, SUPPORT_EFFECT)

    def test_lighting_color_mode(self):
        self.assertEqual(self.backlight.color_mode, COLOR_MODE_UNKNOWN)
        self.assertEqual(self.flame.color_mode, COLOR_MODE_UNKNOWN)

    def test_lighting_is_on(self):
        self.assertTrue(self.backlight.is_on)
        self.assertTrue(self.flame.is_on)

    def test_lighting_brightness(self):
        self.assertIsNone(self.backlight.brightness)
        self.assertIsNone(self.flame.brightness)

    def test_backlight_effect_list(self):
        self.assertCountEqual(
            self.backlight.effect_list,
            [
                "white",
                "blue",
                "orange",
                "whiteblue",
                "whiteorange",
                "blueorange",
            ],
        )

    def test_flame_effect_list(self):
        self.assertCountEqual(
            self.flame.effect_list,
            [
                "orange",
                "red",
                "green",
                "blue",
                "redgreen",
                "redblue",
                "bluegreen",
                "redorange",
                "greenorange",
                "blueorange",
            ],
        )

    def test_backlight_effect(self):
        self.dps[BACKLIGHT_DPS] = "orange"
        self.assertEqual(self.backlight.effect, "orange")

    def test_flame_effect(self):
        self.dps[FLAME_DPS] = "bluegreen"
        self.assertEqual(self.flame.effect, "bluegreen")

    async def test_set_backlight_effect(self):
        async with assert_device_properties_set(
            self.backlight._device,
            {BACKLIGHT_DPS: "whiteblue"},
        ):
            await self.backlight.async_turn_on(effect="whiteblue")

    async def test_set_flame_effect(self):
        async with assert_device_properties_set(
            self.flame._device,
            {FLAME_DPS: "red"},
        ):
            await self.flame.async_turn_on(effect="red")
