from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import BWT_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
ERROR_DPS = "9"


class TestBWTHeatpump(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("bwt_heatpump.yaml")
        climate = cfg.primary_entity
        self.climate_name = climate.name
        self.subject = TuyaLocalClimate(self.mock_device, climate)
        self.dps = BWT_HEATPUMP_PAYLOAD.copy()

        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    @skip("Icon customisation not supported yet")
    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:hot-tub")
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac_off")

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
            self.subject._device, {PRESET_DPS: "cool"}
        ):
            await self.subject.async_set_temperature(preset_mode="Smart Cooling")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 26, PRESET_DPS: "heat"}
        ):
            await self.subject.async_set_temperature(
                temperature=26, preset_mode="Smart Heating"
            )

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

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
        self.dps[PRESET_DPS] = "heat"
        self.assertEqual(self.subject.preset_mode, "Smart Heating")

        self.dps[PRESET_DPS] = "cool"
        self.assertEqual(self.subject.preset_mode, "Smart Cooling")

        self.dps[PRESET_DPS] = "quickheat"
        self.assertEqual(self.subject.preset_mode, "Boost Heating")

        self.dps[PRESET_DPS] = "quickcool"
        self.assertEqual(self.subject.preset_mode, "Boost Cooling")

        self.dps[PRESET_DPS] = "quietheat"
        self.assertEqual(self.subject.preset_mode, "Eco Heating")

        self.dps[PRESET_DPS] = "quietcool"
        self.assertEqual(self.subject.preset_mode, "Eco Cooling")

        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Auto")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [
                "Smart Heating",
                "Boost Heating",
                "Eco Heating",
                "Smart Cooling",
                "Boost Cooling",
                "Eco Cooling",
                "Auto",
            ],
        )

    async def test_set_preset_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "heat"},
        ):
            await self.subject.async_set_preset_mode("Smart Heating")

    async def test_set_preset_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "cool"},
        ):
            await self.subject.async_set_preset_mode("Smart Cooling")

    async def test_set_preset_mode_to_quickheat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quickheat"},
        ):
            await self.subject.async_set_preset_mode("Boost Heating")

    async def test_set_preset_mode_to_quickcool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quickcool"},
        ):
            await self.subject.async_set_preset_mode("Boost Cooling")

    async def test_set_preset_mode_to_quietheat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quietheat"},
        ):
            await self.subject.async_set_preset_mode("Eco Heating")

    async def test_set_preset_mode_to_quietcool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quietcool"},
        ):
            await self.subject.async_set_preset_mode("Eco Cooling")

    async def test_set_preset_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("Auto")

    def test_error_state(self):
        self.dps[ERROR_DPS] = 0
        self.assertEqual(self.subject.device_state_attributes, {"error": "OK"})

        self.dps[ERROR_DPS] = 1
        self.assertEqual(
            self.subject.device_state_attributes,
            {"error": "Water Flow Protection"},
        )
        self.dps[ERROR_DPS] = 2
        self.assertEqual(
            self.subject.device_state_attributes,
            {"error": 2},
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
