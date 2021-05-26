"""Tests for the light entity."""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from custom_components.tuya_local.const import (
    CONF_CLIMATE,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_AUTO,
    CONF_TYPE_GPPH_HEATER,
    CONF_TYPE_GSH_HEATER,
    DOMAIN,
)
from custom_components.tuya_local.heater.climate import GoldairHeater
from custom_components.tuya_local.helpers.device_config import config_for_legacy_use
from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.climate import async_setup_entry

from .const import GSH_HEATER_PAYLOAD
from .helpers import assert_device_properties_set

GSH_HVACMODE_DPS = "1"
GSH_TEMPERATURE_DPS = "2"
GSH_CURRENTTEMP_DPS = "3"
GSH_PRESET_DPS = "4"
GSH_ERROR_DPS = "12"


async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TYPE: CONF_TYPE_AUTO, CONF_DEVICE_ID: "dummy"},
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()
    m_device.async_inferred_type = AsyncMock(return_value=CONF_TYPE_GPPH_HEATER)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"][CONF_CLIMATE]) == GoldairHeater
    m_add_entities.assert_called_once()


class TestTuyaLocalClimate(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        gsh_heater_config = config_for_legacy_use(CONF_TYPE_GSH_HEATER)
        climate = gsh_heater_config.primary_entity
        self.climate_name = climate.name
        self.subject = TuyaLocalClimate(self.mock_device(), climate)
        self.dps = GSH_HEATER_PAYLOAD.copy()

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

    def test_icon(self):
        self.dps[GSH_HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[GSH_HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[GSH_TEMPERATURE_DPS] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {GSH_TEMPERATURE_DPS: 24}
        ):
            await self.subject.async_set_temperature(temperature=24)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {GSH_PRESET_DPS: "low"}
        ):
            await self.subject.async_set_temperature(preset_mode="Low")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {GSH_TEMPERATURE_DPS: 26, GSH_PRESET_DPS: "high"}
        ):
            await self.subject.async_set_temperature(temperature=26, preset_mode="High")

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {GSH_TEMPERATURE_DPS: 25},
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device, {GSH_TEMPERATURE_DPS: 23}
        ):
            await self.subject.async_set_target_temperature(22.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(4\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(36\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    def test_current_temperature(self):
        self.dps[GSH_CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[GSH_HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[GSH_HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[GSH_HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {GSH_HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {GSH_HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[GSH_PRESET_DPS] = "low"
        self.assertEqual(self.subject.preset_mode, "Low")

        self.dps[GSH_PRESET_DPS] = "high"
        self.assertEqual(self.subject.preset_mode, "High")

        self.dps[GSH_PRESET_DPS] = "af"
        self.assertEqual(self.subject.preset_mode, "Anti-freeze")

        self.dps[GSH_PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["Low", "High", "Anti-freeze"])

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {GSH_PRESET_DPS: "low"},
        ):
            await self.subject.async_set_preset_mode("Low")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {GSH_PRESET_DPS: "high"},
        ):
            await self.subject.async_set_preset_mode("High")

    async def test_set_preset_mode_to_af(self):
        async with assert_device_properties_set(
            self.subject._device,
            {GSH_PRESET_DPS: "af"},
        ):
            await self.subject.async_set_preset_mode("Anti-freeze")

    def test_error_state(self):
        # There are currently no known error states; update this as they're discovered
        self.dps[GSH_ERROR_DPS] = "something"
        self.assertEqual(self.subject.device_state_attributes, {"error": "something"})

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
