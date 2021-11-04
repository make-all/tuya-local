from homeassistant.components.climate.const import (
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.components.light import COLOR_MODE_ONOFF
from homeassistant.components.switch import DEVICE_CLASS_SWITCH
from homeassistant.const import STATE_UNAVAILABLE

from ..const import PURLINE_M100_HEATER_PAYLOAD
from ..helpers import (
    assert_device_properties_set,
    assert_device_properties_set_optional,
)
from .base_device_tests import BasicSwitchTests, TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "5"
LIGHTOFF_DPS = "10"
TIMERHR_DPS = "11"
TIMER_DPS = "12"
SWITCH_DPS = "101"
SWING_DPS = "102"


class TestPulineM100Heater(BasicSwitchTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("purline_m100_heater.yaml", PURLINE_M100_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        # BasicLightTests mixin not used due to inverted switch
        self.light = self.entities.get("light_display")
        self.setUpBasicSwitch(
            SWITCH_DPS, self.entities.get("switch_open_window_detector")
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.icon, "mdi:fan")

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
        self.assertEqual(self.subject.min_temp, 15)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 25}
        ):
            await self.subject.async_set_temperature(temperature=25)

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
            ValueError, "temperature \\(4\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(36\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_FAN_ONLY],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set_optional(
            self.subject._device,
            {HVACMODE_DPS: True},
            {PRESET_DPS: "auto"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    async def test_turn_on_fan(self):
        async with assert_device_properties_set_optional(
            self.subject._device,
            {HVACMODE_DPS: True},
            {PRESET_DPS: "off"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Auto")

        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.preset_mode, "Fan")

        self.dps[PRESET_DPS] = "4"
        self.assertEqual(self.subject.preset_mode, "4")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Fan", "1", "2", "3", "4", "5", "Auto"],
        )

    async def test_set_preset_mode_numeric(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "3"},
        ):
            await self.subject.async_set_preset_mode("3")

    def test_swing_mode(self):
        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, SWING_VERTICAL)

        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            [SWING_OFF, SWING_VERTICAL],
        )

    async def test_set_swing_mode_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: True}
        ):
            await self.subject.async_set_swing_mode(SWING_VERTICAL)

    async def test_set_swing_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: False}
        ):
            await self.subject.async_set_swing_mode(SWING_OFF)

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, COLOR_MODE_ONOFF)

    def test_light_icon(self):
        self.dps[LIGHTOFF_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-on")

        self.dps[LIGHTOFF_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-off")

    def test_light_is_on(self):
        self.dps[LIGHTOFF_DPS] = False
        self.assertTrue(self.light.is_on)

        self.dps[LIGHTOFF_DPS] = True
        self.assertFalse(self.light.is_on)

    def test_light_state_attributes(self):
        self.assertEqual(self.light.device_state_attributes, {})

    async def test_light_turn_on(self):
        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: False}
        ):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: True}
        ):
            await self.light.async_turn_off()

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[LIGHTOFF_DPS] = True

        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: False}
        ):
            await self.light.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[LIGHTOFF_DPS] = False

        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: True}
        ):
            await self.light.async_toggle()
