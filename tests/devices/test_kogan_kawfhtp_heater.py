from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..const import KOGAN_KAWFHTP_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import BasicLockTests, TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "3"
CURRENTTEMP_DPS = "4"
TIMER_DPS = "5"
PRESET_DPS = "7"
LOCK_DPS = "2"


class TestGoldairKoganKAHTPHeater(BasicLockTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("kogan_kawfhtp_heater.yaml", KOGAN_KAWFHTP_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))

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
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 40)

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
            ValueError, "temperature \\(4\\) must be between 5 and 40"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(41\\) must be between 5 and 40"
        ):
            await self.subject.async_set_target_temperature(41)

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
        self.dps[PRESET_DPS] = "Low"
        self.assertEqual(self.subject.preset_mode, "Low")

        self.dps[PRESET_DPS] = "High"
        self.assertEqual(self.subject.preset_mode, "High")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["Low", "High"])

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Low"},
        ):
            await self.subject.async_set_preset_mode("Low")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "High"},
        ):
            await self.subject.async_set_preset_mode("High")

    def test_state_attributes(self):
        self.dps[TIMER_DPS] = 10
        self.assertDictEqual(self.subject.device_state_attributes, {"timer": 10})
