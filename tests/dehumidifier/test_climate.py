from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    FAN_HIGH,
    FAN_LOW,
    HVAC_MODE_DRY,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from custom_components.tuya_local.dehumidifier.climate import GoldairDehumidifier
from custom_components.tuya_local.dehumidifier.const import (
    ATTR_AIR_CLEAN_ON,
    ATTR_DEFROSTING,
    ATTR_ERROR,
    ATTR_ERROR_CODE,
    ATTR_TARGET_HUMIDITY,
    ERROR_CODE_TO_DPS_CODE,
    ERROR_TANK,
    FAN_MODE_TO_DPS_MODE,
    HVAC_MODE_TO_DPS_MODE,
    PRESET_AIR_CLEAN,
    PRESET_DRY_CLOTHES,
    PRESET_HIGH,
    PRESET_LOW,
    PRESET_MODE_TO_DPS_MODE,
    PRESET_NORMAL,
    PROPERTY_TO_DPS_ID,
)

from ..const import DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set


class TestGoldairDehumidifier(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = GoldairDehumidifier(self.mock_device())

        self.dps = DEHUMIDIFIER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_HUMIDITY | SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_icon_is_always_standard_when_off_without_error(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False

        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = False
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

    def test_icon_is_purifier_when_air_clean_is_active(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True

        self.assertEqual(self.subject.icon, "mdi:air-purifier")

    def test_icon_is_tshirt_when_dry_clothes_is_active(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]

        self.assertEqual(self.subject.icon, "mdi:tshirt-crew-outline")

    def test_icon_is_always_melting_snowflake_when_defrosting_and_tank_not_full(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = True

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

    def test_icon_is_always_tank_when_tank_full_error_is_present(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = ERROR_CODE_TO_DPS_CODE[ERROR_TANK]

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = True
        self.assertEqual(self.subject.icon, "mdi:cup-water")

    def test_current_humidity(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HUMIDITY]] = 47
        self.assertEqual(self.subject.current_humidity, 47)

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity_in_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY]] = 53

        self.assertEqual(self.subject.target_humidity, 53)

    def test_target_humidity_outside_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY]] = 53

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        self.assertIs(self.subject.target_humidity, None)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        self.assertIs(self.subject.target_humidity, None)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertIs(self.subject.target_humidity, None)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        self.assertIs(self.subject.target_humidity, None)

    async def test_set_target_humidity_in_normal_preset_rounds_up_to_5_percent(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]

        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY]: 55},
        ):
            await self.subject.async_set_humidity(53)

    async def test_set_target_humidity_in_normal_preset_rounds_down_to_5_percent(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]

        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY]: 50},
        ):
            await self.subject.async_set_humidity(52)

    async def test_set_target_humidity_raises_error_outside_of_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        with self.assertRaisesRegex(
            ValueError, "Target humidity can only be changed while in Normal mode"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        with self.assertRaisesRegex(
            ValueError, "Target humidity can only be changed while in Normal mode"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        with self.assertRaisesRegex(
            ValueError, "Target humidity can only be changed while in Normal mode"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        with self.assertRaisesRegex(
            ValueError, "Target humidity can only be changed while in Normal mode"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        with self.assertRaisesRegex(
            ValueError, "Target humidity can only be changed while in Normal mode"
        ):
            await self.subject.async_set_humidity(50)

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_minimum_target_temperature(self):
        self.assertIs(self.subject.min_temp, None)

    def test_maximum_target_temperature(self):
        self.assertIs(self.subject.max_temp, None)

    def test_current_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE]] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_DRY)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_DRY])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_DRY)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_NORMAL)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_LOW)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_DRY_CLOTHES)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None
        self.assertEqual(self.subject.preset_mode, None)

    def test_air_clean_is_surfaced_in_preset_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True

        self.assertEqual(self.subject.preset_mode, PRESET_AIR_CLEAN)

    def test_preset_modes(self):
        self.assertEqual(
            self.subject.preset_modes,
            [
                PRESET_NORMAL,
                PRESET_LOW,
                PRESET_HIGH,
                PRESET_DRY_CLOTHES,
                PRESET_AIR_CLEAN,
            ],
        )

    async def test_set_test_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_NORMAL
                ],
                PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]: False,
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_NORMAL)
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_test_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_LOW
                ],
                PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]: False,
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_LOW)
            self.subject._device.anticipate_property_value.assert_called_once_with(
                PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_LOW
            )

    async def test_set_test_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_HIGH
                ],
                PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]: False,
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_HIGH)
            self.subject._device.anticipate_property_value.assert_called_once_with(
                PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH
            )

    async def test_set_test_preset_mode_to_dry_clothes(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_DRY_CLOTHES
                ],
                PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]: False,
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_DRY_CLOTHES)
            self.subject._device.anticipate_property_value.assert_called_once_with(
                PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH
            )

    async def test_set_test_preset_mode_to_air_clean(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]: True}
        ):
            await self.subject.async_set_preset_mode(PRESET_AIR_CLEAN)
            self.subject._device.anticipate_property_value.assert_called_once_with(
                PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH
            )

    def test_fan_mode_is_forced_to_high_in_high_dry_clothes_air_clean_presets(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = FAN_MODE_TO_DPS_MODE[FAN_LOW]

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)

    def test_fan_mode_is_forced_to_low_in_low_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = FAN_MODE_TO_DPS_MODE[FAN_HIGH]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]

        self.assertEqual(self.subject.fan_mode, FAN_LOW)

    def test_fan_mode_reflects_dps_mode_in_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = FAN_MODE_TO_DPS_MODE[FAN_LOW]
        self.assertEqual(self.subject.fan_mode, FAN_LOW)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = FAN_MODE_TO_DPS_MODE[FAN_HIGH]
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = None
        self.assertEqual(self.subject.fan_mode, None)

    def test_fan_modes_reflect_preset_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.fan_modes, [FAN_LOW, FAN_HIGH])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        self.assertEqual(self.subject.fan_modes, [FAN_LOW])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        self.assertEqual(self.subject.fan_modes, [FAN_HIGH])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        self.assertEqual(self.subject.fan_modes, [FAN_HIGH])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        self.assertEqual(self.subject.fan_modes, [FAN_HIGH])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = False
        self.assertEqual(self.subject.fan_modes, [])

    async def test_set_fan_mode_to_low_succeeds_in_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]: FAN_MODE_TO_DPS_MODE[FAN_LOW]},
        ):
            await self.subject.async_set_fan_mode(FAN_LOW)

    async def test_set_fan_mode_to_high_succeeds_in_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]: FAN_MODE_TO_DPS_MODE[FAN_HIGH]},
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

    async def test_set_fan_mode_fails_with_invalid_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        with self.assertRaisesRegex(ValueError, "Invalid fan mode: something"):
            await self.subject.async_set_fan_mode("something")

    async def test_set_fan_mode_fails_outside_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_LOW
        ]
        with self.assertRaisesRegex(
            ValueError, "Fan mode can only be changed while in Normal preset mode"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_HIGH
        ]
        with self.assertRaisesRegex(
            ValueError, "Fan mode can only be changed while in Normal preset mode"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_DRY_CLOTHES
        ]
        with self.assertRaisesRegex(
            ValueError, "Fan mode can only be changed while in Normal preset mode"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON]] = True
        with self.assertRaisesRegex(
            ValueError, "Fan mode can only be changed while in Normal preset mode"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

    def test_tank_full_or_missing(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = None
        self.assertEqual(self.subject.tank_full_or_missing, False)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = ERROR_CODE_TO_DPS_CODE[ERROR_TANK]
        self.assertEqual(self.subject.tank_full_or_missing, True)

    def test_defrosting(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = False
        self.assertEqual(self.subject.defrosting, False)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = True
        self.assertEqual(self.subject.defrosting, True)

    def test_device_state_attributes(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = False
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                ATTR_ERROR_CODE: None,
                ATTR_ERROR: STATE_UNAVAILABLE,
                ATTR_DEFROSTING: False,
            },
        )

        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = ERROR_CODE_TO_DPS_CODE[ERROR_TANK]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = False
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                ATTR_ERROR: ERROR_TANK,
                ATTR_ERROR_CODE: ERROR_CODE_TO_DPS_CODE[ERROR_TANK],
                ATTR_DEFROSTING: False,
            },
        )

        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = True
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                ATTR_ERROR_CODE: None,
                ATTR_ERROR: STATE_UNAVAILABLE,
                ATTR_DEFROSTING: True,
            },
        )

        self.dps[PROPERTY_TO_DPS_ID[ATTR_ERROR]] = ERROR_CODE_TO_DPS_CODE[ERROR_TANK]
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DEFROSTING]] = True
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                ATTR_ERROR: ERROR_TANK,
                ATTR_ERROR_CODE: ERROR_CODE_TO_DPS_CODE[ERROR_TANK],
                ATTR_DEFROSTING: True,
            },
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
