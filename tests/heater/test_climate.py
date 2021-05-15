from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from custom_components.tuya_local.heater.climate import GoldairHeater
from custom_components.tuya_local.heater.const import (
    ATTR_ECO_TARGET_TEMPERATURE,
    ATTR_ERROR,
    ATTR_ERROR_CODE,
    ATTR_POWER_LEVEL,
    ATTR_POWER_MODE,
    ATTR_POWER_MODE_AUTO,
    ATTR_POWER_MODE_USER,
    ATTR_TARGET_TEMPERATURE,
    HVAC_MODE_TO_DPS_MODE,
    POWER_LEVEL_AUTO,
    POWER_LEVEL_STOP,
    POWER_LEVEL_TO_DPS_LEVEL,
    PRESET_MODE_TO_DPS_MODE,
    PROPERTY_TO_DPS_ID,
    STATE_ANTI_FREEZE,
    STATE_COMFORT,
    STATE_ECO,
)

from ..const import GPPH_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set


class TestGoldairHeater(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = GoldairHeater(self.mock_device())

        self.dps = GPPH_HEATER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
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

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_STOP
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]] = 25
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ECO_TARGET_TEMPERATURE]] = 15

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_COMFORT
        ]
        self.assertEqual(self.subject.target_temperature, 25)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ECO
        ]
        self.assertEqual(self.subject.target_temperature, 15)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ANTI_FREEZE
        ]
        self.assertIs(self.subject.target_temperature, None)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_COMFORT
        ]
        self.assertEqual(self.subject.min_temp, 5)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ECO
        ]
        self.assertEqual(self.subject.min_temp, 5)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ANTI_FREEZE
        ]
        self.assertIs(self.subject.min_temp, None)

    def test_maximum_target_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_COMFORT
        ]
        self.assertEqual(self.subject.max_temp, 35)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ECO
        ]
        self.assertEqual(self.subject.max_temp, 21)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ANTI_FREEZE
        ]
        self.assertIs(self.subject.max_temp, None)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25}
        ):
            await self.subject.async_set_temperature(temperature=25)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    STATE_COMFORT
                ]
            },
        ):
            await self.subject.async_set_temperature(preset_mode=STATE_COMFORT)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25,
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    STATE_COMFORT
                ],
            },
        ):
            await self.subject.async_set_temperature(
                temperature=25, preset_mode=STATE_COMFORT
            )

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature_in_comfort_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_COMFORT
        ]

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25}
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_in_eco_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ECO
        ]

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_ECO_TARGET_TEMPERATURE]: 15}
        ):
            await self.subject.async_set_target_temperature(15)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25},
        ):
            await self.subject.async_set_target_temperature(24.6)

    async def test_set_target_temperature_fails_outside_valid_range_in_comfort(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_COMFORT
        ]

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(4\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(36\\) must be between 5 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    async def test_set_target_temperature_fails_outside_valid_range_in_eco(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ECO
        ]

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(4\\) must be between 5 and 21"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(22\\) must be between 5 and 21"
        ):
            await self.subject.async_set_target_temperature(22)

    async def test_set_target_temperature_fails_in_anti_freeze(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ANTI_FREEZE
        ]

        with self.assertRaisesRegex(
            ValueError, "You cannot set the temperature in Anti-freeze mode"
        ):
            await self.subject.async_set_target_temperature(25)

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
            STATE_COMFORT
        ]
        self.assertEqual(self.subject.preset_mode, STATE_COMFORT)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ECO
        ]
        self.assertEqual(self.subject.preset_mode, STATE_ECO)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            STATE_ANTI_FREEZE
        ]
        self.assertEqual(self.subject.preset_mode, STATE_ANTI_FREEZE)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertEqual(
            self.subject.preset_modes, [STATE_COMFORT, STATE_ECO, STATE_ANTI_FREEZE]
        )

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    STATE_COMFORT
                ]
            },
        ):
            await self.subject.async_set_preset_mode(STATE_COMFORT)

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[STATE_ECO]},
        ):
            await self.subject.async_set_preset_mode(STATE_ECO)

    async def test_set_preset_mode_to_anti_freeze(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    STATE_ANTI_FREEZE
                ]
            },
        ):
            await self.subject.async_set_preset_mode(STATE_ANTI_FREEZE)

    def test_power_level_returns_user_power_level(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_MODE]] = ATTR_POWER_MODE_USER

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_TO_DPS_LEVEL[
            "Stop"
        ]
        self.assertEqual(self.subject.swing_mode, "Stop")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_TO_DPS_LEVEL["3"]
        self.assertEqual(self.subject.swing_mode, "3")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_TO_DPS_LEVEL[
            "Auto"
        ]
        self.assertEqual(self.subject.swing_mode, "Auto")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = None
        self.assertIs(self.subject.swing_mode, None)

    def test_power_level_in_returns_power_mode_when_not_in_user_power_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_MODE]] = POWER_LEVEL_TO_DPS_LEVEL["Stop"]
        self.assertEqual(self.subject.swing_mode, "Stop")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_MODE]] = POWER_LEVEL_TO_DPS_LEVEL["3"]
        self.assertEqual(self.subject.swing_mode, "3")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_MODE]] = POWER_LEVEL_TO_DPS_LEVEL["Auto"]
        self.assertEqual(self.subject.swing_mode, "Auto")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_MODE]] = None
        self.assertIs(self.subject.swing_mode, None)

    def test_power_levels(self):
        self.assertEqual(
            self.subject.swing_modes,
            ["Stop", "1", "2", "3", "4", "5", "Auto"],
        )

    async def test_set_power_level_to_stop(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]: POWER_LEVEL_TO_DPS_LEVEL["Stop"]},
        ):
            await self.subject.async_set_swing_mode("Stop")

    async def test_set_power_level_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]: POWER_LEVEL_TO_DPS_LEVEL["Auto"]},
        ):
            await self.subject.async_set_swing_mode("Auto")

    async def test_set_power_level_to_numeric_value(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]: POWER_LEVEL_TO_DPS_LEVEL["3"]},
        ):
            await self.subject.async_set_swing_mode("3")

    async def test_set_power_level_to_invalid_value_raises_error(self):
        with self.assertRaisesRegex(ValueError, "Invalid power level: unknown"):
            await self.subject.async_set_swing_mode("unknown")

    def test_error_state(self):
        # There are currently no known error states; update this as they're discovered
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = "something"
        self.assertEqual(
            self.subject.device_state_attributes,
            {ATTR_ERROR_CODE: "something", ATTR_ERROR: "Error something"},
        )

    def test_no_error_state(self):
        # Test that no error is OK
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = 0
        self.assertEqual(
            self.subject.device_state_attributes,
            {ATTR_ERROR_CODE: 0, ATTR_ERROR: "OK"},
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
