from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.light import (
    ColorMode,
    LightEntityFeature,
)
from homeassistant.const import UnitOfTemperature

from ..const import KOGAN_KASHMFP20BA_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
PRESET_DPS = "2"
TEMPERATURE_DPS = "3"
CURRENTTEMP_DPS = "4"
BACKLIGHT_DPS = "5"
FLAME_DPS = "6"


class TestKoganKASHMF20BAHeater(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "kogan_kashmfp20ba_heater.yaml", KOGAN_KASHMFP20BA_HEATER_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=10,
            max=30,
        )
        self.backlight = self.entities.get("light_backlight")
        self.flame = self.entities.get("light_flame")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

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

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

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

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})
        self.assertEqual(self.backlight.extra_state_attributes, {})
        self.assertEqual(self.flame.extra_state_attributes, {})

    def test_lighting_supported_color_modes(self):
        self.assertCountEqual(self.backlight.supported_color_modes, [])
        self.assertCountEqual(self.flame.supported_color_modes, [])

    def test_lighting_supported_features(self):
        self.assertEqual(self.backlight.supported_features, LightEntityFeature.EFFECT)
        self.assertEqual(self.flame.supported_features, LightEntityFeature.EFFECT)

    def test_lighting_color_mode(self):
        self.assertEqual(self.backlight.color_mode, ColorMode.UNKNOWN)
        self.assertEqual(self.flame.color_mode, ColorMode.UNKNOWN)

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
