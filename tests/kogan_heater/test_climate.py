from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from custom_components.tuya_local.kogan_heater.climate import KoganHeater
from custom_components.tuya_local.kogan_heater.const import (
    ATTR_TARGET_TEMPERATURE,
    ATTR_TIMER,
    HVAC_MODE_TO_DPS_MODE,
    PRESET_HIGH,
    PRESET_LOW,
    PRESET_MODE_TO_DPS_MODE,
    PROPERTY_TO_DPS_ID,
)

from ..const import KOGAN_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set


class TestKoganHeater(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = KoganHeater(self.mock_device())

        self.dps = KOGAN_HEATER_PAYLOAD.copy()
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
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 15)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25}
        ):
            await self.subject.async_set_temperature(temperature=25)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[PRESET_LOW]},
        ):
            await self.subject.async_set_temperature(preset_mode=PRESET_LOW)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25,
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_LOW
                ],
            },
        ):
            await self.subject.async_set_temperature(
                temperature=25, preset_mode=PRESET_LOW
            )

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25}
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25},
        ):
            await self.subject.async_set_target_temperature(24.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(14\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(14)

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(36\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    def test_current_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE]] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_LOW)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertEqual(self.subject.preset_modes, [PRESET_LOW, PRESET_HIGH])

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[PRESET_LOW]},
        ):
            await self.subject.async_set_preset_mode(PRESET_LOW)

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_HIGH
                ]
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_HIGH)

    def test_device_state_attributes(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TIMER]] = 1
        self.assertEqual(
            self.subject.device_state_attributes,
            {ATTR_TIMER: 1},
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
