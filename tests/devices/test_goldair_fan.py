from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_SLEEP,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SWING_HORIZONTAL,
    SWING_OFF,
)
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import FAN_PAYLOAD
from ..helpers import assert_device_properties_set

HVACMODE_DPS = "1"
FANMODE_DPS = "2"
PRESET_DPS = "3"
SWING_DPS = "8"
UNKNOWN_DPS = "11"
LIGHT_DPS = "101"


class TestGoldairFan(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("goldair_fan.yaml")
        climate = cfg.primary_entity
        light = None
        for e in cfg.secondary_entities():
            if e.entity == "light":
                light = e
        self.climate_name = climate.name
        self.light_name = light.name

        self.subject = TuyaLocalClimate(self.mock_device(), climate)
        self.light = TuyaLocalLight(self.mock_device(), light)

        self.dps = FAN_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)
        self.assertTrue(self.light.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)
        self.assertEqual(self.light.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.climate_name)
        self.assertEqual(self.light.friendly_name, self.light_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.light.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)
        self.assertEqual(self.light.device_info, self.subject._device.device_info)

    @skip("Icon customisation not supported yet")
    def test_icon_is_fan(self):
        self.assertEqual(self.subject.icon, "mdi:fan")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.subject.preset_mode, PRESET_ECO)

        self.dps[PRESET_DPS] = PRESET_SLEEP
        self.assertEqual(self.subject.preset_mode, PRESET_SLEEP)

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes, ["normal", PRESET_ECO, PRESET_SLEEP]
        )

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "nature"},
        ):
            await self.subject.async_set_preset_mode(PRESET_ECO)

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: PRESET_SLEEP},
        ):
            await self.subject.async_set_preset_mode(PRESET_SLEEP)

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, SWING_HORIZONTAL)

        self.dps[SWING_DPS] = None
        self.assertIs(self.subject.swing_mode, None)

    def test_swing_modes(self):
        self.assertCountEqual(self.subject.swing_modes, [SWING_OFF, SWING_HORIZONTAL])

    async def test_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode(SWING_OFF)

    async def test_set_swing_mode_to_horizontal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode(SWING_HORIZONTAL)

    @skip("Conditions not supported yet")
    def test_fan_modes(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertCountEqual(self.subject.fan_modes, list(range(1, 13)))

        self.dps[PRESET_DPS] = "nature"
        self.assertCountEqual(self.subject.fan_modes, [1, 2, 3])

        self.dps[PRESET_DPS] = PRESET_SLEEP
        self.assertCountEqual(self.subject.fan_modes, [1, 2, 3])

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.fan_modes, [])

    @skip("Conditions not supported yet")
    def test_fan_mode_for_normal_preset(self):
        self.dps[PRESET_DPS] = "normal"

        self.dps[FANMODE_DPS] = "1"
        self.assertEqual(self.subject.fan_mode, 1)

        self.dps[FANMODE_DPS] = "6"
        self.assertEqual(self.subject.fan_mode, 6)

        self.dps[FANMODE_DPS] = "12"
        self.assertEqual(self.subject.fan_mode, 12)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.subject.fan_mode, None)

    @skip("Conditions not supported yet")
    async def test_set_fan_mode_for_normal_preset(self):
        self.dps[PRESET_DPS] = "normal"

        async with assert_device_properties_set(
            self.subject._device,
            {FANMODE_DPS: "6"},
        ):
            await self.subject.async_set_fan_mode(6)

    @skip("Conditions not supported yet")
    def test_fan_mode_for_eco_preset(self):
        self.dps[PRESET_DPS] = "nature"

        self.dps[FANMODE_DPS] = "4"
        self.assertEqual(self.subject.fan_mode, 1)

        self.dps[FANMODE_DPS] = "8"
        self.assertEqual(self.subject.fan_mode, 2)

        self.dps[FANMODE_DPS] = "12"
        self.assertEqual(self.subject.fan_mode, 3)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.subject.fan_mode, None)

    @skip("Conditions not supported yet")
    async def test_set_fan_mode_for_eco_preset(self):
        self.dps[PRESET_DPS] = "nature"

        async with assert_device_properties_set(
            self.subject._device,
            {FANMODE_DPS: "4"},
        ):
            await self.subject.async_set_fan_mode(1)

    @skip("Conditions not supported yet")
    def test_fan_mode_for_sleep_preset(self):
        self.dps[PRESET_DPS] = PRESET_SLEEP

        self.dps[FANMODE_DPS] = "4"
        self.assertEqual(self.subject.fan_mode, 1)

        self.dps[FANMODE_DPS] = "8"
        self.assertEqual(self.subject.fan_mode, 2)

        self.dps[FANMODE_DPS] = "12"
        self.assertEqual(self.subject.fan_mode, 3)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.subject.fan_mode, None)

    @skip("Conditions not supported yet")
    async def test_set_fan_mode_for_sleep_preset(self):
        self.dps[PRESET_DPS] = PRESET_SLEEP

        async with assert_device_properties_set(
            self.subject._device,
            {FANMODE_DPS: "8"},
        ):
            await self.subject.async_set_fan_mode(2)

    @skip("Conditions not supported yet")
    async def test_set_fan_mode_does_nothing_when_preset_mode_is_not_set(self):
        self.dps[PRESET_DPS] = None

        with self.assertRaises(
            ValueError, msg="Fan mode can only be set when a preset mode is set"
        ):
            await self.subject.async_set_fan_mode(2)

    def test_device_state_attributes(self):
        self.dps[UNKNOWN_DPS] = "something"
        self.assertEqual(
            self.subject.device_state_attributes, {"unknown_11": "something"}
        )

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

    async def test_light_update(self):
        result = AsyncMock()
        self.light._device.async_refresh.return_value = result()

        await self.light.async_update()

        self.light._device.async_refresh.assert_called_once()
        result.assert_awaited()
