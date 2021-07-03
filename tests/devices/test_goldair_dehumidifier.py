from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    FAN_HIGH,
    FAN_LOW,
    HVAC_MODE_DRY,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
)
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.generic.fan import TuyaLocalFan
from custom_components.tuya_local.generic.humidifier import TuyaLocalHumidifier
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.generic.lock import TuyaLocalLock
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set

HVACMODE_DPS = "1"
PRESET_DPS = "2"
HUMIDITY_DPS = "4"
AIRCLEAN_DPS = "5"
FANMODE_DPS = "6"
LOCK_DPS = "7"
ERROR_DPS = "11"
UNKNOWN12_DPS = "12"
UNKNOWN101_DPS = "101"
LIGHTOFF_DPS = "102"
CURRENTTEMP_DPS = "103"
CURRENTHUMID_DPS = "104"
DEFROST_DPS = "105"

PRESET_NORMAL = "0"
PRESET_LOW = "1"
PRESET_HIGH = "2"
PRESET_DRY_CLOTHES = "3"

ERROR_TANK = "Tank full or missing"


class TestGoldairDehumidifier(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("goldair_dehumidifier.yaml")
        entities = {}
        entities[cfg.primary_entity.entity] = cfg.primary_entity

        for e in cfg.secondary_entities():
            entities[e.entity] = e

        self.climate_name = (
            "missing" if "climate" not in entities else entities["climate"].name
        )
        self.light_name = (
            "missing" if "light" not in entities else entities["light"].name
        )
        self.lock_name = "missing" if "lock" not in entities else entities["lock"].name
        self.humidifier_name = (
            "missing" if "humidifier" not in entities else entities["humidifier"].name
        )
        self.fan_name = "missing" if "fan" not in entities else entities["fan"].name

        self.subject = TuyaLocalClimate(self.mock_device(), entities.get("climate"))
        self.light = TuyaLocalLight(self.mock_device(), entities.get("light"))
        self.lock = TuyaLocalLock(self.mock_device(), entities.get("lock"))
        self.humidifier = TuyaLocalHumidifier(
            self.mock_device(), entities.get("humidifier")
        )
        self.fan = TuyaLocalFan(self.mock_device(), entities.get("fan"))

        self.dps = DEHUMIDIFIER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_HUMIDITY | SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)
        self.assertTrue(self.fan.should_poll)
        self.assertTrue(self.light.should_poll)
        self.assertTrue(self.lock.should_poll)
        self.assertTrue(self.humidifier.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)
        self.assertEqual(self.fan.name, self.subject._device.name)
        self.assertEqual(self.light.name, self.subject._device.name)
        self.assertEqual(self.lock.name, self.subject._device.name)
        self.assertEqual(self.humidifier.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.climate_name)
        self.assertEqual(self.fan.friendly_name, self.fan_name)
        self.assertEqual(self.light.friendly_name, self.light_name)
        self.assertEqual(self.lock.friendly_name, self.lock_name)
        self.assertEqual(self.humidifier.friendly_name, self.humidifier_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.fan.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.light.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.lock.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.humidifier.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)
        self.assertEqual(self.fan.device_info, self.subject._device.device_info)
        self.assertEqual(self.light.device_info, self.subject._device.device_info)
        self.assertEqual(self.lock.device_info, self.subject._device.device_info)
        self.assertEqual(self.humidifier.device_info, self.subject._device.device_info)

    def test_icon_is_always_standard_when_off_without_error(self):
        self.dps[ERROR_DPS] = None
        self.dps[HVACMODE_DPS] = False

        self.dps[AIRCLEAN_DPS] = False
        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[AIRCLEAN_DPS] = True
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

    @skip("Conditions not included in config")
    def test_icon_is_purifier_when_air_clean_is_active(self):
        self.dps[ERROR_DPS] = None
        self.dps[HVACMODE_DPS] = True
        self.dps[AIRCLEAN_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-purifier")

    def test_icon_is_tshirt_when_dry_clothes_is_active(self):
        self.dps[ERROR_DPS] = None
        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.icon, "mdi:tshirt-crew-outline")

    def test_icon_is_always_melting_snowflake_when_defrosting_and_tank_not_full(self):
        self.dps[DEFROST_DPS] = True

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

        self.dps[AIRCLEAN_DPS] = True
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

    def test_icon_is_always_tank_when_tank_full_error_is_present(self):
        self.dps[ERROR_DPS] = 8

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[AIRCLEAN_DPS] = True
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.assertEqual(self.subject.icon, "mdi:cup-water")

        self.dps[DEFROST_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:cup-water")

    def test_current_humidity(self):
        self.dps[CURRENTHUMID_DPS] = 47
        self.assertEqual(self.subject.current_humidity, 47)

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)
        self.assertEqual(self.humidifier.min_humidity, 30)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)
        self.assertEqual(self.humidifier.max_humidity, 80)

    def test_target_humidity_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.dps[HUMIDITY_DPS] = 55

        self.assertEqual(self.subject.target_humidity, 55)

    def test_target_humidity_in_humidifier(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.dps[HUMIDITY_DPS] = 45

        self.assertEqual(self.humidifier.target_humidity, 45)

    def test_target_humidity_outside_normal_preset(self):
        self.dps[HUMIDITY_DPS] = 55

        self.dps[PRESET_DPS] = PRESET_HIGH
        self.assertIs(self.subject.target_humidity, None)

        self.dps[PRESET_DPS] = PRESET_LOW
        self.assertIs(self.subject.target_humidity, None)

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertIs(self.subject.target_humidity, None)

        # self.dps[PRESET_DPS] = PRESET_NORMAL
        # self.dps[AIRCLEAN_DPS] = True
        # self.assertIs(self.subject.target_humidity, None)

    async def test_set_target_humidity_in_normal_preset_rounds_up_to_5_percent(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 55},
        ):
            await self.subject.async_set_humidity(53)

    async def test_set_target_humidity_in_normal_preset_rounds_down_to_5_percent(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL

        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 50},
        ):
            await self.subject.async_set_humidity(52)

    async def test_set_humidity_in_humidifier_rounds_up_to_5_percent(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.humidifier._device,
            {HUMIDITY_DPS: 45},
        ):
            await self.humidifier.async_set_humidity(43)

    async def test_set_humidity_in_humidifier_rounds_down_to_5_percent(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.humidifier._device,
            {HUMIDITY_DPS: 40},
        ):
            await self.humidifier.async_set_humidity(42)

    async def test_set_target_humidity_raises_error_outside_of_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_LOW
        with self.assertRaisesRegex(
            AttributeError, "humidity cannot be set at this time"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PRESET_DPS] = PRESET_HIGH
        with self.assertRaisesRegex(
            AttributeError, "humidity cannot be set at this time"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PRESET_DPS] = PRESET_LOW
        with self.assertRaisesRegex(
            AttributeError, "humidity cannot be set at this time"
        ):
            await self.subject.async_set_humidity(50)

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        with self.assertRaisesRegex(
            AttributeError, "humidity cannot be set at this time"
        ):
            await self.subject.async_set_humidity(50)

        # self.dps[PRESET_DPS] = PRESET_NORMAL
        # self.dps[AIRCLEAN_DPS] = True
        # with self.assertRaisesRegex(
        #     AttributeError, "humidity cannot be set at this time"
        # ):
        #     await self.subject.async_set_humidity(50)

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_minimum_target_temperature(self):
        self.assertIs(self.subject.min_temp, None)

    def test_maximum_target_temperature(self):
        self.assertIs(self.subject.max_temp, None)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_DRY)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_DRY])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_DRY)

    async def test_turn_off(self):

        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_humidifier_is_on(self):
        self.dps[HVACMODE_DPS] = True
        self.assertTrue(self.humidifier.is_on)

        self.dps[HVACMODE_DPS] = False
        self.assertFalse(self.humidifier.is_on)

    async def test_dehumidifier_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.humidifier.async_turn_on()

    async def test_dehumidifier_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.humidifier.async_turn_off()

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.assertEqual(self.subject.preset_mode, "Normal")
        self.assertEqual(self.humidifier.mode, "Normal")

        self.dps[PRESET_DPS] = PRESET_LOW
        self.assertEqual(self.subject.preset_mode, "Low")
        self.assertEqual(self.humidifier.mode, "Low")

        self.dps[PRESET_DPS] = PRESET_HIGH
        self.assertEqual(self.subject.preset_mode, "High")
        self.assertEqual(self.humidifier.mode, "High")

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.preset_mode, "Dry clothes")
        self.assertEqual(self.humidifier.mode, "Dry clothes")

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.preset_mode, None)
        self.assertEqual(self.humidifier.mode, None)

    @skip("Conditions not included in config")
    def test_air_clean_is_surfaced_in_preset_mode(self):
        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.dps[AIRCLEAN_DPS] = True

        self.assertEqual(self.subject.preset_mode, "Air clean")

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [
                "Normal",
                "Low",
                "High",
                "Dry clothes",
                #                "Air clean",
            ],
        )

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: PRESET_NORMAL,
            },
        ):
            await self.subject.async_set_preset_mode("Normal")
            self.subject._device.anticipate_property_value.assert_not_called()

    @skip("Conditions not included in config")
    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: PRESET_LOW,
            },
        ):
            await self.subject.async_set_preset_mode("Low")
            self.subject._device.anticipate_property_value.assert_called_once_with(
                FANMODE_DPS, "1"
            )

    @skip("Conditions not included in config")
    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: PRESET_HIGH,
            },
        ):
            await self.subject.async_set_preset_mode("High")
            self.subject._device.anticipate_property_value.assert_called_once_with(
                FANMODE_DPS, "3"
            )

    @skip("Conditions not included in config")
    async def test_set_preset_mode_to_dry_clothes(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: PRESET_DRY_CLOTHES,
            },
        ):
            await self.subject.async_set_preset_mode("Dry clothes")
            self.subject._device.anticipate_property_value.assert_called_once_with(
                FANMODE_DPS, "3"
            )

    @skip("Conditions not included in config")
    async def test_set_preset_mode_to_air_clean(self):
        async with assert_device_properties_set(
            self.subject._device, {AIRCLEAN_DPS: True}
        ):
            await self.subject.async_set_preset_mode("Air clean")
            self.subject._device.anticipate_property_value.assert_called_once_with(
                FANMODE_DPS, "1"
            )

    @skip("Conditions not included in config")
    def test_fan_mode_is_forced_to_high_in_high_dry_clothes_air_clean_presets(self):
        self.dps[FANMODE_DPS] = "1"
        self.dps[PRESET_DPS] = PRESET_HIGH
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)
        self.assertEqual(self.fan.percentage, 100)

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)
        self.assertEqual(self.fan.percentage, 100)

        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.dps[AIRCLEAN_DPS] = True
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)
        self.assertEqual(self.subject.percentage, 100)

    @skip("Conditions not included in config")
    def test_fan_mode_is_forced_to_low_in_low_preset(self):
        self.dps[FANMODE_DPS] = "3"
        self.dps[PRESET_DPS] = PRESET_LOW

        self.assertEqual(self.subject.fan_mode, FAN_LOW)
        self.assertEqual(self.fan.percentage, 50)

    def test_fan_mode_reflects_dps_mode_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.dps[FANMODE_DPS] = "1"
        self.assertEqual(self.subject.fan_mode, FAN_LOW)
        self.assertEqual(self.fan.percentage, 50)

        self.dps[FANMODE_DPS] = "3"
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)
        self.assertEqual(self.fan.percentage, 100)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.subject.fan_mode, None)
        self.assertEqual(self.fan.percentage, None)

    @skip("Conditions not included in config")
    def test_fan_modes_reflect_preset_mode(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.assertCountEqual(self.subject.fan_modes, [FAN_LOW, FAN_HIGH])
        self.assertEqual(self.fan.speed_count, 2)

        self.dps[PRESET_DPS] = PRESET_LOW
        self.assertEqual(self.subject.fan_modes, [FAN_LOW])
        self.assertEqual(self.fan.speed_count, 0)

        self.dps[PRESET_DPS] = PRESET_HIGH
        self.assertEqual(self.subject.fan_modes, [FAN_HIGH])
        self.assertEqual(self.fan.speed_count, 0)

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.fan_modes, [FAN_HIGH])
        self.assertEqual(self.fan.speed_count, 0)

        # self.dps[PRESET_DPS] = PRESET_NORMAL
        # self.dps[AIRCLEAN_DPS] = True
        # self.assertEqual(self.subject.fan_modes, [FAN_HIGH])
        # self.assertEqual(self.fan.speed_count, 0)

    async def test_set_fan_mode_to_low_succeeds_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.subject._device,
            {FANMODE_DPS: "1"},
        ):
            await self.subject.async_set_fan_mode(FAN_LOW)

    async def test_set_fan_mode_to_high_succeeds_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.subject._device,
            {FANMODE_DPS: "3"},
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

    async def test_set_fan_50_succeeds_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "1"},
        ):
            await self.fan.async_set_percentage(50)

    async def test_set_fan_100_succeeds_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "3"},
        ):
            await self.fan.async_set_percentage(100)

    async def test_set_fan_30_snaps_to_50_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "1"},
        ):
            await self.fan.async_set_percentage(30)

    @skip("Restriction to listed options not supported yet")
    async def test_set_fan_mode_fails_with_invalid_mode(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        with self.assertRaisesRegex(ValueError, "Invalid fan mode: something"):
            await self.subject.async_set_fan_mode("something")

    @skip("Conditions not yet supported for setting")
    async def test_set_fan_mode_fails_outside_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_LOW
        with self.assertRaisesRegex(
            AttributeError, "fan_mode cannot be set at this time"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

        self.dps[PRESET_DPS] = PRESET_HIGH
        with self.assertRaisesRegex(
            AttributeError, "fan_mode cannot be set at this time"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        with self.assertRaisesRegex(
            AttributeError, "fan_mode cannot be set at this time"
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

        # self.dps[PRESET_DPS] = PRESET_NORMAL
        # self.dps[AIRCLEAN_DPS] = True
        # with self.assertRaisesRegex(
        #     ValueError, "Fan mode can only be changed while in Normal preset mode"
        # ):
        #     await self.subject.async_set_fan_mode(FAN_HIGH)

    def test_device_state_attributes(self):
        self.dps[ERROR_DPS] = None
        self.dps[DEFROST_DPS] = False
        self.dps[AIRCLEAN_DPS] = False
        self.dps[UNKNOWN12_DPS] = "something"
        self.dps[UNKNOWN101_DPS] = False
        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "error": STATE_UNAVAILABLE,
                "defrosting": False,
                "air_clean_on": False,
                "unknown_12": "something",
                "unknown_101": False,
            },
        )

        self.dps[ERROR_DPS] = 8
        self.dps[DEFROST_DPS] = True
        self.dps[AIRCLEAN_DPS] = True
        self.dps[UNKNOWN12_DPS] = "something else"
        self.dps[UNKNOWN101_DPS] = True
        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "error": ERROR_TANK,
                "defrosting": True,
                "air_clean_on": True,
                "unknown_12": "something else",
                "unknown_101": True,
            },
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()

    def test_lock_was_created(self):
        self.assertIsInstance(self.lock, TuyaLocalLock)

    def test_lock_is_same_device(self):
        self.assertEqual(self.lock._device, self.subject._device)

    def test_lock_state(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.lock.state, STATE_LOCKED)

        self.dps[LOCK_DPS] = False
        self.assertEqual(self.lock.state, STATE_UNLOCKED)

        self.dps[LOCK_DPS] = None
        self.assertEqual(self.lock.state, STATE_UNAVAILABLE)

    def test_lock_is_locked(self):
        self.dps[LOCK_DPS] = True
        self.assertTrue(self.lock.is_locked)

        self.dps[LOCK_DPS] = False
        self.assertFalse(self.lock.is_locked)

        self.dps[LOCK_DPS] = None
        self.assertFalse(self.lock.is_locked)

    async def async_test_lock_locks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: True}):
            await self.subject.async_lock()

    async def async_test_lock_unlocks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: False}):
            await self.subject.async_unlock()

    async def async_test_lock_update(self):
        result = AsyncMock()
        self.lock._device.async_refresh.return_value = result()

        await self.lock.async_update()

        self.lock._device.async_refresh.assert_called_once()
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
