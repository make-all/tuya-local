from unittest import skip

from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED

from homeassistant.const import STATE_UNAVAILABLE

from ..const import GPPH_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
LOCK_DPS = "6"
ERROR_DPS = "12"
POWERLEVEL_DPS = "101"
TIMER_DPS = "102"
TIMERACT_DPS = "103"
LIGHT_DPS = "104"
SWING_DPS = "105"
ECOTEMP_DPS = "106"


class TestGoldairHeater(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("goldair_gpph_heater.yaml", GPPH_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.light = self.entities.get("light")
        self.lock = self.entities.get("lock")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

        self.dps[HVACMODE_DPS] = True
        self.dps[POWERLEVEL_DPS] = "stop"
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_in_eco_and_af_modes(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.dps[ECOTEMP_DPS] = 15

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.target_temperature, 15)

        self.dps[PRESET_DPS] = "AF"
        self.assertIs(self.subject.target_temperature, None)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_temperature(self):
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.min_temp, 5)

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.min_temp, 5)

        self.dps[PRESET_DPS] = "AF"
        self.assertIs(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.max_temp, 35)

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.max_temp, 21)

        self.dps[PRESET_DPS] = "AF"
        self.assertIs(self.subject.max_temp, 5)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 25}
        ):
            await self.subject.async_set_temperature(temperature=25)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "C"}
        ):
            await self.subject.async_set_temperature(preset_mode="comfort")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 25,
                PRESET_DPS: "C",
            },
        ):
            await self.subject.async_set_temperature(
                temperature=25, preset_mode="comfort"
            )

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature_in_comfort_mode(self):
        self.dps[PRESET_DPS] = "C"

        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 25}
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_in_eco_mode(self):
        self.dps[PRESET_DPS] = "ECO"

        async with assert_device_properties_set(
            self.subject._device, {ECOTEMP_DPS: 15}
        ):
            await self.subject.async_set_target_temperature(15)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25},
        ):
            await self.subject.async_set_target_temperature(24.6)

    async def test_set_target_temperature_fails_outside_valid_range_in_comfort(self):
        self.dps[PRESET_DPS] = "C"

        with self.assertRaisesRegex(
            ValueError, "temperature \\(4\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(36\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    async def test_set_target_temperature_fails_outside_valid_range_in_eco(self):
        self.dps[PRESET_DPS] = "ECO"

        with self.assertRaisesRegex(
            ValueError, "eco_temperature \\(4\\) must be between 5 and 21"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "eco_temperature \\(22\\) must be between 5 and 21"
        ):
            await self.subject.async_set_target_temperature(22)

    async def test_set_target_temperature_fails_in_anti_freeze(self):
        self.dps[PRESET_DPS] = "AF"

        with self.assertRaisesRegex(
            AttributeError, "temperature cannot be set at this time"
        ):
            await self.subject.async_set_target_temperature(25)

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
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.preset_mode, "comfort")

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.preset_mode, "eco")

        self.dps[PRESET_DPS] = "AF"
        self.assertEqual(self.subject.preset_mode, "away")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["comfort", "eco", "away"])

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "C"},
        ):
            await self.subject.async_set_preset_mode("comfort")

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "ECO"},
        ):
            await self.subject.async_set_preset_mode("eco")

    async def test_set_preset_mode_to_anti_freeze(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "AF"},
        ):
            await self.subject.async_set_preset_mode("away")

    def test_power_level_returns_user_power_level(self):
        self.dps[SWING_DPS] = "user"

        self.dps[POWERLEVEL_DPS] = "stop"
        self.assertEqual(self.subject.swing_mode, "Stop")

        self.dps[POWERLEVEL_DPS] = "3"
        self.assertEqual(self.subject.swing_mode, "3")

    def test_non_user_swing_mode(self):
        self.dps[SWING_DPS] = "stop"
        self.assertEqual(self.subject.swing_mode, "Stop")

        self.dps[SWING_DPS] = "auto"
        self.assertEqual(self.subject.swing_mode, "Auto")

        self.dps[SWING_DPS] = None
        self.assertIs(self.subject.swing_mode, None)

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            ["Stop", "1", "2", "3", "4", "5", "Auto"],
        )

    @skip("Paired settings not supported yet")
    async def test_set_power_level_to_stop(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWERLEVEL_DPS: "stop"},
        ):
            await self.subject.async_set_swing_mode("Stop")

    async def test_set_swing_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: "auto"},
        ):
            await self.subject.async_set_swing_mode("Auto")

    async def test_set_power_level_to_numeric_value(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: "user", POWERLEVEL_DPS: "3"},
        ):
            await self.subject.async_set_swing_mode("3")

    @skip("Restriction to mapped values not supported yet")
    async def test_set_power_level_to_invalid_value_raises_error(self):
        with self.assertRaisesRegex(ValueError, "Invalid power level: unknown"):
            await self.subject.async_set_swing_mode("unknown")

    def test_device_state_attributes(self):
        self.dps[ERROR_DPS] = "something"
        self.dps[TIMER_DPS] = 5
        self.dps[TIMERACT_DPS] = True
        self.dps[POWERLEVEL_DPS] = 4

        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "error": "something",
                "timer": 5,
                "timer_mode": True,
                "power_level": 4,
            },
        )

    def test_lock_state(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.lock.state, STATE_LOCKED)

        self.dps[LOCK_DPS] = False
        self.assertEqual(self.lock.state, STATE_UNLOCKED)

        self.dps[LOCK_DPS] = None
        self.assertEqual(self.lock.state, STATE_UNAVAILABLE)

    def test_lock_is_locked(self):
        self.dps[LOCK_DPS] = True
        self.assertTrue(self.lock.is_locked)

        self.dps[LOCK_DPS] = False
        self.assertFalse(self.lock.is_locked)

        self.dps[LOCK_DPS] = None
        self.assertFalse(self.lock.is_locked)

    async def test_lock_locks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: True}):
            await self.lock.async_lock()

    async def test_lock_unlocks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: False}):
            await self.lock.async_unlock()

    def test_light_icon(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-off")

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.is_on, True)

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.is_on, False)

    def test_light_state_attributes(self):
        self.assertEqual(self.light.device_state_attributes, {})

    async def test_light_turn_on(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_turn_off()

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[LIGHT_DPS] = False

        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[LIGHT_DPS] = True

        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_toggle()
