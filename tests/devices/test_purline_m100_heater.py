from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import AsyncMock, patch

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
from homeassistant.components.switch import DEVICE_CLASS_SWITCH
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.generic.switch import TuyaLocalSwitch
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import PURLINE_M100_HEATER_PAYLOAD
from ..helpers import (
    assert_device_properties_set,
    assert_device_properties_set_optional,
)

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "5"
LIGHTOFF_DPS = "10"
TIMERHR_DPS = "11"
TIMER_DPS = "12"
SWITCH_DPS = "101"
SWING_DPS = "102"


class TestPulineM100Heater(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("purline_m100_heater.yaml")
        climate = cfg.primary_entity
        light = None
        switch = None
        for e in cfg.secondary_entities():
            if e.entity == "light":
                light = e
            elif e.entity == "switch":
                switch = e
        self.climate_name = climate.name
        self.light_name = "missing" if light is None else light.name
        self.switch_name = "missing" if switch is None else switch.name
        self.subject = TuyaLocalClimate(self.mock_device(), climate)
        self.light = TuyaLocalLight(self.mock_device(), light)
        self.switch = TuyaLocalSwitch(self.mock_device(), switch)

        self.dps = PURLINE_M100_HEATER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)
        self.assertTrue(self.light.should_poll)
        self.assertTrue(self.switch.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)
        self.assertEqual(self.light.name, self.subject._device.name)
        self.assertEqual(self.switch.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.climate_name)
        self.assertEqual(self.light.friendly_name, self.light_name)
        self.assertEqual(self.switch.friendly_name, self.switch_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.light.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.switch.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)
        self.assertEqual(self.light.device_info, self.subject._device.device_info)
        self.assertEqual(self.switch.device_info, self.subject._device.device_info)

    @skip("Icon customisation not supported yet")
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
        self.subject._device.async_set_property.assert_not_called

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
            ValueError, "Target temperature \\(4\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(36\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    @skip("Conditions not supported yet")
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

    @skip("Conditions not supported yet")
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

    @skip("Conditions not supported yet")
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

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()

    def test_light_was_created(self):
        self.assertIsInstance(self.light, TuyaLocalLight)

    def test_light_is_same_device(self):
        self.assertEqual(self.light._device, self.subject._device)

    def test_light_icon(self):
        self.dps[LIGHTOFF_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-on")

        self.dps[LIGHTOFF_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-off")

    def test_light_is_on(self):
        self.dps[LIGHTOFF_DPS] = False
        self.assertEqual(self.light.is_on, True)

        self.dps[LIGHTOFF_DPS] = True
        self.assertEqual(self.light.is_on, False)

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

    async def test_light_update(self):
        result = AsyncMock()
        self.light._device.async_refresh.return_value = result()

        await self.light.async_update()

        self.light._device.async_refresh.assert_called_once()
        result.assert_awaited()

    def test_switch_was_created(self):
        self.assertIsInstance(self.switch, TuyaLocalSwitch)

    def test_switch_is_same_device(self):
        self.assertEqual(self.switch._device, self.subject._device)

    def test_switch_class_is_outlet(self):
        self.assertEqual(self.switch.device_class, DEVICE_CLASS_SWITCH)

    def test_switch_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.switch.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.switch.is_on)

    def test_switch_is_on_when_unavailable(self):
        self.dps[SWITCH_DPS] = None
        self.assertEqual(self.switch.is_on, STATE_UNAVAILABLE)

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: True}
        ):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: False}
        ):
            await self.switch.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[SWITCH_DPS] = False

        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: True}
        ):
            await self.switch.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[SWITCH_DPS] = True

        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: False}
        ):
            await self.switch.async_toggle()

    def test_switch_state_attributes_set(self):
        self.assertEqual(self.switch.device_state_attributes, {})
