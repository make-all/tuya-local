from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_SLEEP,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE as SUPPORT_CLIMATE_PRESET,
    SUPPORT_SWING_MODE,
    SWING_HORIZONTAL,
    SWING_OFF,
)
from homeassistant.components.fan import (
    SUPPORT_OSCILLATE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
)

from homeassistant.const import STATE_UNAVAILABLE
from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.generic.fan import TuyaLocalFan
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import FAN_PAYLOAD
from ..helpers import assert_device_properties_set

HVACMODE_DPS = "1"
FANMODE_DPS = "2"
PRESET_DPS = "3"
SWING_DPS = "8"
TIMER_DPS = "11"
LIGHT_DPS = "101"


class TestGoldairFan(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("goldair_fan.yaml")
        entities = {}
        entities[cfg.primary_entity.entity] = cfg.primary_entity
        for e in cfg.secondary_entities():
            entities[e.entity] = e

        self.climate_name = (
            "missing" if "climate" not in entities.keys() else entities["climate"].name
        )
        self.fan_name = (
            "missing" if "fan" not in entities.keys() else entities["fan"].name
        )
        self.light_name = (
            "missing" if "light" not in entities.keys() else entities["light"].name
        )

        self.subject = TuyaLocalFan(self.mock_device(), entities.get("fan"))
        self.climate = TuyaLocalClimate(self.mock_device(), entities.get("climate"))
        self.light = TuyaLocalLight(self.mock_device(), entities.get("light"))

        self.dps = FAN_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_OSCILLATE | SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED,
        )
        self.assertEqual(
            self.climate.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_CLIMATE_PRESET | SUPPORT_SWING_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)
        self.assertTrue(self.climate.should_poll)
        self.assertTrue(self.light.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)
        self.assertEqual(self.climate.name, self.subject._device.name)
        self.assertEqual(self.light.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.fan_name)
        self.assertEqual(self.climate.friendly_name, self.climate_name)
        self.assertEqual(self.light.friendly_name, self.light_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.climate.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.light.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)
        self.assertEqual(self.climate.device_info, self.subject._device.device_info)
        self.assertEqual(self.light.device_info, self.subject._device.device_info)

    @skip("Icon customisation not supported yet")
    def test_climate_icon_is_fan(self):
        self.assertEqual(self.climate.icon, "mdi:fan")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.climate.temperature_unit, self.climate._device.temperature_unit
        )

    def test_is_on(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.climate.hvac_mode, HVAC_MODE_FAN_ONLY)
        self.assertTrue(self.subject.is_on)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.climate.hvac_mode, HVAC_MODE_OFF)
        self.assertFalse(self.subject.is_on)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.climate.hvac_mode, STATE_UNAVAILABLE)
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    def test_climate_hvac_modes(self):
        self.assertCountEqual(
            self.climate.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY]
        )

    async def test_climate_turn_on(self):
        async with assert_device_properties_set(
            self.climate._device, {HVACMODE_DPS: True}
        ):
            await self.climate.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    async def test_climate_turn_off(self):
        async with assert_device_properties_set(
            self.climate._device, {HVACMODE_DPS: False}
        ):
            await self.climate.async_set_hvac_mode(HVAC_MODE_OFF)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_turn_off()

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.climate.preset_mode, "normal")
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.climate.preset_mode, PRESET_ECO)
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = PRESET_SLEEP
        self.assertEqual(self.climate.preset_mode, PRESET_SLEEP)
        self.assertEqual(self.subject.preset_mode, PRESET_SLEEP)

        self.dps[PRESET_DPS] = None
        self.assertIs(self.climate.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.climate.preset_modes, ["normal", PRESET_ECO, PRESET_SLEEP]
        )
        self.assertCountEqual(self.subject.preset_modes, ["normal", "nature", "sleep"])

    async def test_set_climate_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.climate._device,
            {PRESET_DPS: "normal"},
        ):
            await self.climate.async_set_preset_mode("normal")

    async def test_set_climate_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.climate._device,
            {PRESET_DPS: "nature"},
        ):
            await self.climate.async_set_preset_mode(PRESET_ECO)

    async def test_set_climate_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.climate._device,
            {PRESET_DPS: PRESET_SLEEP},
        ):
            await self.climate.async_set_preset_mode(PRESET_SLEEP)

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_nature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "nature"},
        ):
            await self.subject.async_set_preset_mode("nature")

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.climate.swing_mode, SWING_OFF)
        self.assertFalse(self.subject.oscillating)

        self.dps[SWING_DPS] = True
        self.assertEqual(self.climate.swing_mode, SWING_HORIZONTAL)
        self.assertTrue(self.subject.oscillating)

        self.dps[SWING_DPS] = None
        self.assertIs(self.climate.swing_mode, None)
        self.assertFalse(self.subject.oscillating)

    def test_swing_modes(self):
        self.assertCountEqual(self.climate.swing_modes, [SWING_OFF, SWING_HORIZONTAL])

    async def test_climate_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.climate._device,
            {SWING_DPS: False},
        ):
            await self.climate.async_set_swing_mode(SWING_OFF)

    async def test_climate_set_swing_mode_to_horizontal(self):
        async with assert_device_properties_set(
            self.climate._device,
            {SWING_DPS: True},
        ):
            await self.climate.async_set_swing_mode(SWING_HORIZONTAL)

    async def test_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: False}
        ):
            await self.subject.async_oscillate(False)

    async def test_oscillate_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: True}
        ):
            await self.subject.async_oscillate(True)

    def test_speed(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[FANMODE_DPS] = 6
        self.assertEqual(self.subject.percentage, 50)

    async def test_set_speed_in_normal_mode(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 3}):
            await self.subject.async_set_percentage(25)

    async def test_set_speed_in_normal_mode_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(
            self.subject._device, {FANMODE_DPS: 10}
        ):
            await self.subject.async_set_percentage(80)

    @skip("Complex conditions not supported yet")
    async def test_set_speed_in_sleep_mode_snaps(self):
        self.dps[PRESET_DPS] = "sleep"
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 8}):
            await self.subject.async_set_percentage(75)

    @skip("Complex conditions not supported yet")
    def test_climate_fan_modes(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertCountEqual(self.climate.fan_modes, list(range(1, 13)))

        self.dps[PRESET_DPS] = "nature"
        self.assertCountEqual(self.climate.fan_modes, [1, 2, 3])

        self.dps[PRESET_DPS] = PRESET_SLEEP
        self.assertCountEqual(self.climate.fan_modes, [1, 2, 3])

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.climate.fan_modes, [])

    @skip("Complex conditions not supported yet")
    def test_climate_fan_mode_for_normal_preset(self):
        self.dps[PRESET_DPS] = "normal"

        self.dps[FANMODE_DPS] = "1"
        self.assertEqual(self.climate.fan_mode, 1)

        self.dps[FANMODE_DPS] = "6"
        self.assertEqual(self.climate.fan_mode, 6)

        self.dps[FANMODE_DPS] = "12"
        self.assertEqual(self.climate.fan_mode, 12)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    @skip("Complex conditions not supported yet")
    async def test_climate_set_fan_mode_for_normal_preset(self):
        self.dps[PRESET_DPS] = "normal"

        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: "6"},
        ):
            await self.climate.async_set_fan_mode(6)

    @skip("Complex conditions not supported yet")
    def test_climate_fan_mode_for_eco_preset(self):
        self.dps[PRESET_DPS] = "nature"

        self.dps[FANMODE_DPS] = "4"
        self.assertEqual(self.climate.fan_mode, 1)

        self.dps[FANMODE_DPS] = "8"
        self.assertEqual(self.climate.fan_mode, 2)

        self.dps[FANMODE_DPS] = "12"
        self.assertEqual(self.climate.fan_mode, 3)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    @skip("Complex conditions not supported yet")
    async def test_climate_set_fan_mode_for_eco_preset(self):
        self.dps[PRESET_DPS] = "nature"

        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: "4"},
        ):
            await self.climate.async_set_fan_mode(1)

    @skip("Complex conditions not supported yet")
    def test_climate_fan_mode_for_sleep_preset(self):
        self.dps[PRESET_DPS] = PRESET_SLEEP

        self.dps[FANMODE_DPS] = "4"
        self.assertEqual(self.climate.fan_mode, 1)

        self.dps[FANMODE_DPS] = "8"
        self.assertEqual(self.climate.fan_mode, 2)

        self.dps[FANMODE_DPS] = "12"
        self.assertEqual(self.climate.fan_mode, 3)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    @skip("Complex conditions not supported yet")
    async def test_climate_set_fan_mode_for_sleep_preset(self):
        self.dps[PRESET_DPS] = PRESET_SLEEP

        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: "8"},
        ):
            await self.climate.async_set_fan_mode(2)

    @skip("Complex conditions not supported yet")
    async def test_climate_set_fan_mode_does_nothing_when_preset_mode_is_not_set(self):
        self.dps[PRESET_DPS] = None

        with self.assertRaises(
            ValueError, msg="Fan mode can only be set when a preset mode is set"
        ):
            await self.climate.async_set_fan_mode(2)

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.assertEqual(self.climate.device_state_attributes, {"timer": "5"})
        self.assertEqual(self.climate.device_state_attributes, {"timer": "5"})

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
