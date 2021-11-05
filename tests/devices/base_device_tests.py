from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch, PropertyMock
from uuid import uuid4

from homeassistant.components.light import COLOR_MODE_ONOFF
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.components.switch import DEVICE_CLASS_SWITCH
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.generic.binary_sensor import TuyaLocalBinarySensor
from custom_components.tuya_local.generic.climate import TuyaLocalClimate
from custom_components.tuya_local.generic.fan import TuyaLocalFan
from custom_components.tuya_local.generic.humidifier import TuyaLocalHumidifier
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.generic.lock import TuyaLocalLock
from custom_components.tuya_local.generic.number import TuyaLocalNumber
from custom_components.tuya_local.generic.select import TuyaLocalSelect
from custom_components.tuya_local.generic.sensor import TuyaLocalSensor
from custom_components.tuya_local.generic.switch import TuyaLocalSwitch

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    possible_matches,
)

from ..helpers import assert_device_properties_set

DEVICE_TYPES = {
    "binary_sensor": TuyaLocalBinarySensor,
    "climate": TuyaLocalClimate,
    "fan": TuyaLocalFan,
    "humidifier": TuyaLocalHumidifier,
    "light": TuyaLocalLight,
    "lock": TuyaLocalLock,
    "number": TuyaLocalNumber,
    "switch": TuyaLocalSwitch,
    "select": TuyaLocalSelect,
    "sensor": TuyaLocalSensor,
}


class TuyaDeviceTestCase(IsolatedAsyncioTestCase):
    __test__ = False

    def setUpForConfig(self, config_file, payload):
        """Perform setup tasks for every test."""
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        self.dps = payload.copy()
        self.mock_device.get_property.side_effect = lambda id: self.dps[id]
        cfg = TuyaDeviceConfig(config_file)
        self.conf_type = cfg.legacy_type
        type(self.mock_device).has_returned_state = PropertyMock(return_value=True)
        type(self.mock_device).unique_id = PropertyMock(return_value=str(uuid4()))
        self.mock_device.name = cfg.name

        self.entities = {}
        self.entities[cfg.primary_entity.config_id] = self.create_entity(
            cfg.primary_entity
        )

        self.names = {}
        self.names[cfg.primary_entity.config_id] = cfg.primary_entity.name(cfg.name)
        for e in cfg.secondary_entities():
            self.entities[e.config_id] = self.create_entity(e)
            self.names[e.config_id] = e.name(cfg.name)

    def create_entity(self, config):
        """Create an entity to match the config"""
        dev_type = DEVICE_TYPES[config.entity]
        if dev_type:
            return dev_type(self.mock_device, config)

    def test_config_matched(self):
        for cfg in possible_matches(self.dps):
            if cfg.legacy_type == self.conf_type:
                self.assertEqual(cfg.match_quality(self.dps), 100.0)
                return
        self.fail()

    def test_should_poll(self):
        for e in self.entities.values():
            self.assertTrue(e.should_poll)

    def test_available(self):
        for e in self.entities.values():
            self.assertTrue(e.available)

    def test_name_returns_device_name(self):
        for e in self.entities:
            self.assertEqual(self.entities[e].name, self.names[e])

    def test_unique_id_contains_device_unique_id(self):
        entities = {}
        for e in self.entities.values():
            self.assertIn(self.mock_device.unique_id, e.unique_id)
            if type(e) not in entities:
                entities[type(e)] = []

            entities[type(e)].append(e.unique_id)

        for e in entities.values():
            self.assertCountEqual(e, set(e))

    def test_device_info_returns_device_info_from_device(self):
        for e in self.entities.values():
            self.assertEqual(e.device_info, self.mock_device.device_info)

    async def test_update(self):
        for e in self.entities.values():
            result = AsyncMock()
            self.mock_device.async_refresh.return_value = result()
            self.mock_device.async_refresh.reset_mock()
            await e.async_update()
            self.mock_device.async_refresh.assert_called_once()
            result.assert_awaited()


# Mixins for common test functions


class SwitchableTests:
    def setUpSwitchable(self, dps, subject):
        self.switch_dps = dps
        self.switch_subject = subject

    def test_switchable_is_on(self):
        self.dps[self.switch_dps] = True
        self.assertTrue(self.switch_subject.is_on)

        self.dps[self.switch_dps] = False
        self.assertFalse(self.switch_subject.is_on)

        self.dps[self.switch_dps] = None
        self.assertIsNone(self.switch_subject.is_on)

    async def test_switchable_turn_on(self):
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: True}
        ):
            await self.switch_subject.async_turn_on()

    async def test_switchable_turn_off(self):
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: False}
        ):
            await self.switch_subject.async_turn_off()

    async def test_switchable_toggle(self):
        self.dps[self.switch_dps] = False
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: True}
        ):
            await self.switch_subject.async_toggle()

        self.dps[self.switch_dps] = True
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: False}
        ):
            await self.switch_subject.async_toggle()


class BasicLightTests:
    def setUpBasicLight(self, dps, subject):
        self.basicLight = subject
        self.basicLightDps = dps

    def test_basic_light_supported_features(self):
        self.assertEqual(self.basicLight.supported_features, 0)

    def test_basic_light_supported_color_modes(self):
        self.assertCountEqual(
            self.basicLight.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_basic_light_color_mode(self):
        self.assertEqual(self.basicLight.color_mode, COLOR_MODE_ONOFF)

    def test_light_has_no_brightness(self):
        self.assertIsNone(self.basicLight.brightness)

    def test_light_has_no_effects(self):
        self.assertIsNone(self.basicLight.effect_list)
        self.assertIsNone(self.basicLight.effect)

    def test_basic_light_is_on(self):
        self.dps[self.basicLightDps] = True
        self.assertTrue(self.basicLight.is_on)
        self.dps[self.basicLightDps] = False
        self.assertFalse(self.basicLight.is_on)

    async def test_basic_light_turn_on(self):
        async with assert_device_properties_set(
            self.basicLight._device, {self.basicLightDps: True}
        ):
            await self.basicLight.async_turn_on()

    async def test_basic_light_turn_off(self):
        async with assert_device_properties_set(
            self.basicLight._device, {self.basicLightDps: False}
        ):
            await self.basicLight.async_turn_off()

    async def test_basic_light_toggle_turns_on_when_it_was_off(self):
        self.dps[self.basicLightDps] = False
        async with assert_device_properties_set(
            self.basicLight._device,
            {self.basicLightDps: True},
        ):
            await self.basicLight.async_toggle()

    async def test_basic_light_toggle_turns_off_when_it_was_on(self):
        self.dps[self.basicLightDps] = True
        async with assert_device_properties_set(
            self.basicLight._device,
            {self.basicLightDps: False},
        ):
            await self.basicLight.async_toggle()

    def test_basic_light_state_attributes(self):
        self.assertEqual(self.basicLight.device_state_attributes, {})


class BasicLockTests:
    def setUpBasicLock(self, dps, subject):
        self.basicLock = subject
        self.basicLockDps = dps

    def test_basic_lock_state(self):
        self.dps[self.basicLockDps] = True
        self.assertEqual(self.basicLock.state, STATE_LOCKED)

        self.dps[self.basicLockDps] = False
        self.assertEqual(self.basicLock.state, STATE_UNLOCKED)

        self.dps[self.basicLockDps] = None
        self.assertEqual(self.basicLock.state, STATE_UNAVAILABLE)

    def test_basic_lock_is_locked(self):
        self.dps[self.basicLockDps] = True
        self.assertTrue(self.basicLock.is_locked)

        self.dps[self.basicLockDps] = False
        self.assertFalse(self.basicLock.is_locked)

        self.dps[self.basicLockDps] = None
        self.assertFalse(self.basicLock.is_locked)

    async def test_basic_lock_locks(self):
        async with assert_device_properties_set(
            self.basicLock._device,
            {self.basicLockDps: True},
        ):
            await self.basicLock.async_lock()

    async def test_basic_lock_unlocks(self):
        async with assert_device_properties_set(
            self.basicLock._device,
            {self.basicLockDps: False},
        ):
            await self.basicLock.async_unlock()

    def test_basic_lock_state_attributes(self):
        self.assertEqual(self.basicLock.device_state_attributes, {})


class BasicSwitchTests:
    def setUpBasicSwitch(self, dps, subject):
        self.basicSwitch = subject
        self.basicSwitchDps = dps

    def test_basic_switch_is_on(self):
        self.dps[self.basicSwitchDps] = True
        self.assertEqual(self.basicSwitch.is_on, True)

        self.dps[self.basicSwitchDps] = False
        self.assertEqual(self.basicSwitch.is_on, False)

    async def test_basic_switch_turn_on(self):
        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: True}
        ):
            await self.basicSwitch.async_turn_on()

    async def test_basic_switch_turn_off(self):
        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: False}
        ):
            await self.basicSwitch.async_turn_off()

    async def test_basic_switch_toggle_turns_on_when_it_was_off(self):
        self.dps[self.basicSwitchDps] = False

        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: True}
        ):
            await self.basicSwitch.async_toggle()

    async def test_basic_switch_toggle_turns_off_when_it_was_on(self):
        self.dps[self.basicSwitchDps] = True

        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: False}
        ):
            await self.basicSwitch.async_toggle()

    def test_basic_switch_class_is_switch(self):
        self.assertEqual(self.basicSwitch.device_class, DEVICE_CLASS_SWITCH)

    def test_basic_switch_has_no_power_monitoring(self):
        self.assertIsNone(self.basicSwitch.current_power_w)

    def test_basic_switch_state_attributes(self):
        self.assertEqual(self.basicSwitch.device_state_attributes, {})
