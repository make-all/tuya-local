from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.fan import SUPPORT_PRESET_MODE
from homeassistant.components.humidifier import SUPPORT_MODES
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.components.switch import DEVICE_CLASS_SWITCH
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.generic.fan import TuyaLocalFan
from custom_components.tuya_local.generic.humidifier import TuyaLocalHumidifier
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.generic.lock import TuyaLocalLock
from custom_components.tuya_local.generic.switch import TuyaLocalSwitch
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import ELECTRIQ_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set

SWITCH_DPS = "1"
MODE_DPS = "2"
CURRENTHUMID_DPS = "3"
HUMIDITY_DPS = "4"
LOCK_DPS = "7"
LIGHT_DPS = "10"
PRESET_DPS = "102"
CURRENTTEMP_DPS = "103"
IONIZER_DPS = "104"


class TestElectriqDehumidifier(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("electriq_dehumidifier.yaml")
        entities = {}
        entities[cfg.primary_entity.entity] = cfg.primary_entity
        for e in cfg.secondary_entities():
            entities[e.entity] = e

        self.humidifier_name = (
            "missing" if "humidifier" not in entities else entities["humidifier"].name
        )
        self.fan_name = "missing" if "fan" not in entities else entities["fan"].name
        self.light_name = (
            "missing" if "light" not in entities else entities["light"].name
        )
        self.lock_name = "missing" if "lock" not in entities else entities["lock"].name
        self.switch_name = (
            "missing" if "switch" not in entities else entities["switch"].name
        )
        self.subject = TuyaLocalHumidifier(
            self.mock_device(), entities.get("humidifier")
        )
        self.fan = TuyaLocalFan(self.mock_device(), entities.get("fan"))
        self.light = TuyaLocalLight(self.mock_device(), entities.get("light"))
        self.lock = TuyaLocalLock(self.mock_device(), entities.get("lock"))
        self.switch = TuyaLocalSwitch(self.mock_device(), entities.get("switch"))
        self.dps = ELECTRIQ_DEHUMIDIFIER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_MODES)
        self.assertEqual(self.fan.supported_features, SUPPORT_PRESET_MODE)

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)
        self.assertTrue(self.fan.should_poll)
        self.assertTrue(self.light.should_poll)
        self.assertTrue(self.lock.should_poll)
        self.assertTrue(self.switch.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)
        self.assertEqual(self.fan.name, self.subject._device.name)
        self.assertEqual(self.light.name, self.subject._device.name)
        self.assertEqual(self.lock.name, self.subject._device.name)
        self.assertEqual(self.switch.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.humidifier_name)
        self.assertEqual(self.fan.friendly_name, self.fan_name)
        self.assertEqual(self.light.friendly_name, self.light_name)
        self.assertEqual(self.lock.friendly_name, self.lock_name)
        self.assertEqual(self.switch.friendly_name, self.switch_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.fan.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.light.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.lock.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.switch.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)
        self.assertEqual(self.fan.device_info, self.subject._device.device_info)
        self.assertEqual(self.light.device_info, self.subject._device.device_info)
        self.assertEqual(self.lock.device_info, self.subject._device.device_info)
        self.assertEqual(self.switch.device_info, self.subject._device.device_info)

    def test_entities_created(self):
        self.assertIsInstance(self.subject, TuyaLocalHumidifier)
        self.assertIsInstance(self.fan, TuyaLocalFan)
        self.assertIsInstance(self.light, TuyaLocalLight)
        self.assertIsInstance(self.lock, TuyaLocalLock)
        self.assertIsInstance(self.switch, TuyaLocalSwitch)

    def test_entities_are_same_device(self):
        self.assertEqual(self.fan._device, self.subject._device)
        self.assertEqual(self.light._device, self.subject._device)
        self.assertEqual(self.lock._device, self.subject._device)
        self.assertEqual(self.switch._device, self.subject._device)

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[MODE_DPS] = "fan"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-purifier")

        self.assertEqual(self.light.icon, "mdi:solar-power")
        self.assertEqual(self.switch.icon, "mdi:creation")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 35)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    async def test_set_target_humidity_rounds_up_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 55},
        ):
            await self.subject.async_set_humidity(53)

    async def test_set_target_humidity_rounds_down_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 50},
        ):
            await self.subject.async_set_humidity(52)

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.assertTrue(self.fan.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)
        self.assertFalse(self.fan.is_on)

        self.dps[SWITCH_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)
        self.assertEqual(self.fan.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    async def test_fan_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.fan.async_turn_on()

    async def test_fan_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.fan.async_turn_off()

    def test_mode(self):
        self.dps[MODE_DPS] = "low"
        self.assertEqual(self.subject.mode, "Low")
        self.dps[MODE_DPS] = "high"
        self.assertEqual(self.subject.mode, "High")
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.mode, "Auto")
        self.dps[MODE_DPS] = "fan"
        self.assertEqual(self.subject.mode, "Air clean")

    async def test_set_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "auto",
            },
        ):
            await self.subject.async_set_mode("Auto")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "low",
            },
        ):
            await self.subject.async_set_mode("Low")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "high",
            },
        ):
            await self.subject.async_set_mode("High")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "fan",
            },
        ):
            await self.subject.async_set_mode("Air clean")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_fan_preset_mode(self):
        self.dps[PRESET_DPS] = "45"
        self.assertEqual(self.fan.preset_mode, "Half open")

        self.dps[PRESET_DPS] = "90"
        self.assertEqual(self.fan.preset_mode, "Fully open")

        self.dps[PRESET_DPS] = "0_90"
        self.assertEqual(self.fan.preset_mode, "Oscillate")

    async def test_set_fan_to_half_open(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "45",
            },
        ):
            await self.fan.async_set_preset_mode("Half open")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_fan_to_fully_open(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "90",
            },
        ):
            await self.fan.async_set_preset_mode("Fully open")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_fan_to_oscillate(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "0_90",
            },
        ):
            await self.fan.async_set_preset_mode("Oscillate")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_lock_is_locked(self):
        self.dps[LOCK_DPS] = True
        self.assertTrue(self.lock.is_locked)

        self.dps[LOCK_DPS] = False
        self.assertFalse(self.lock.is_locked)

        self.dps[LOCK_DPS] = None
        self.assertFalse(self.lock.is_locked)

    async def test_lock_locks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: True}):
            await self.lock.async_lock()

    async def test_lock_unlocks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: False}):
            await self.lock.async_unlock()

    async def test_lock_update(self):
        result = AsyncMock()
        self.lock._device.async_refresh.return_value = result()

        await self.lock.async_update()
        self.lock._device.async_refresh.assert_called_once()
        result.assert_awaited()

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertTrue(self.light.is_on)

        self.dps[LIGHT_DPS] = False
        self.assertFalse(self.light.is_on)

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

    def test_switch_is_on(self):
        self.dps[IONIZER_DPS] = True
        self.assertTrue(self.switch.is_on)

        self.dps[IONIZER_DPS] = False
        self.assertFalse(self.switch.is_on)

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: True}
        ):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: False}
        ):
            await self.switch.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[IONIZER_DPS] = False
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: True}
        ):
            await self.switch.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[IONIZER_DPS] = True
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: False}
        ):
            await self.switch.async_toggle()

    async def test_switch_update(self):
        result = AsyncMock()
        self.switch._device.async_refresh.return_value = result()

        await self.switch.async_update()
        self.switch._device.async_refresh.assert_called_once()
        result.assert_awaited()

    def test_state_attributes(self):
        self.dps[CURRENTHUMID_DPS] = 50
        self.dps[CURRENTTEMP_DPS] = 21
        self.assertCountEqual(
            self.subject.device_state_attributes,
            {"current_humidity": 50, "current_temperature": 21},
        )
        self.assertEqual(self.fan.device_state_attributes, {})
        self.assertEqual(self.light.device_state_attributes, {})
        self.assertEqual(self.lock.device_state_attributes, {})
        self.assertEqual(self.switch.device_state_attributes, {})
