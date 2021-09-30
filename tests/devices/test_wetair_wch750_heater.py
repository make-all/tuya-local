from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_BOOST,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.light import COLOR_MODE_BRIGHTNESS
from homeassistant.const import STATE_UNAVAILABLE

from ..const import WETAIR_WCH750_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
PRESET_DPS = "4"
HVACACTION_DPS = "11"
TIMER_DPS = "19"
COUNTDOWN_DPS = "20"
UNKNOWN21_DPS = "21"
BRIGHTNESS_DPS = "101"


class TestWetairWCH750Heater(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("wetair_wch750_heater.yaml", WETAIR_WCH750_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.light = self.entities.get("light")

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

    def test_temperatre_unit_retrns_device_temperatre_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_in_af_mode(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.dps[PRESET_DPS] = "mod_antiforst"
        self.assertEqual(self.subject.target_temperature, None)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 25}
        ):
            await self.subject.async_set_temperature(temperature=25)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "mod_antiforst"}
        ):
            await self.subject.async_set_temperature(preset_mode=PRESET_AWAY)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25, PRESET_DPS: "mod_max12h"},
        ):
            await self.subject.async_set_temperature(
                preset_mode=PRESET_BOOST, temperature=25
            )

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called()

    async def test_set_target_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 25}
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25},
        ):
            await self.subject.async_set_target_temperature(24.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(4\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(36\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    async def test_set_target_temperature_fails_in_anti_frost(self):
        self.dps[PRESET_DPS] = "mod_antiforst"

        with self.assertRaisesRegex(
            AttributeError, "temperature cannot be set at this time"
        ):
            await self.subject.async_set_target_temperature(25)

    def test_current_temperature_not_supported(self):
        self.assertIsNone(self.subject.current_temperature)

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
            self.subject._device,
            {HVACMODE_DPS: True},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_trn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "mod_free"
        self.assertEqual(self.subject.preset_mode, PRESET_COMFORT)

        self.dps[PRESET_DPS] = "mod_max12h"
        self.assertEqual(self.subject.preset_mode, PRESET_BOOST)

        self.dps[PRESET_DPS] = "mod_antiforst"
        self.assertEqual(self.subject.preset_mode, PRESET_AWAY)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["comfort", "boost", "away"])

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mod_free"},
        ):
            await self.subject.async_set_preset_mode(PRESET_COMFORT)

    async def test_set_preset_mode_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mod_max12h"},
        ):
            await self.subject.async_set_preset_mode(PRESET_BOOST)

    async def test_set_preset_mode_to_away(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mod_antiforst"},
        ):
            await self.subject.async_set_preset_mode(PRESET_AWAY)

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "1h"
        self.dps[COUNTDOWN_DPS] = 20
        self.dps[UNKNOWN21_DPS] = 21

        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "timer": "1h",
                "countdown": 20,
                "unknown_21": 21,
            },
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, COLOR_MODE_BRIGHTNESS)

    def test_light_is_on(self):
        self.dps[BRIGHTNESS_DPS] = "level0"
        self.assertEqual(self.light.is_on, False)

        self.dps[BRIGHTNESS_DPS] = "level1"
        self.assertEqual(self.light.is_on, True)
        self.dps[BRIGHTNESS_DPS] = "level2"
        self.assertEqual(self.light.is_on, True)
        self.dps[BRIGHTNESS_DPS] = "level3"
        self.assertEqual(self.light.is_on, True)

    def test_light_brightness(self):
        self.dps[BRIGHTNESS_DPS] = "level0"
        self.assertEqual(self.light.brightness, 0)

        self.dps[BRIGHTNESS_DPS] = "level1"
        self.assertEqual(self.light.brightness, 85)

        self.dps[BRIGHTNESS_DPS] = "level2"
        self.assertEqual(self.light.brightness, 170)

        self.dps[BRIGHTNESS_DPS] = "level3"
        self.assertEqual(self.light.brightness, 255)

    def test_light_state_attributes(self):
        self.assertEqual(self.light.device_state_attributes, {})

    async def test_light_turn_on(self):
        async with assert_device_properties_set(
            self.light._device, {BRIGHTNESS_DPS: "level3"}
        ):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level0"},
        ):
            await self.light.async_turn_off()

    async def test_light_brightness_to_low(self):
        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level1"},
        ):
            await self.light.async_turn_on(brightness=85)

    async def test_light_brightness_to_mid(self):
        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level2"},
        ):
            await self.light.async_turn_on(brightness=170)

    async def test_light_brightness_to_high(self):
        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level3"},
        ):
            await self.light.async_turn_on(brightness=255)

    async def test_light_brightness_to_off(self):
        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level0"},
        ):
            await self.light.async_turn_on(brightness=0)

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[BRIGHTNESS_DPS] = "level0"

        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level3"},
        ):
            await self.light.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[BRIGHTNESS_DPS] = "level2"

        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level0"},
        ):
            await self.light.async_toggle()

    async def test_light_brightness_snaps(self):
        async with assert_device_properties_set(
            self.light._device,
            {BRIGHTNESS_DPS: "level1"},
        ):
            await self.light.async_turn_on(brightness=100)
