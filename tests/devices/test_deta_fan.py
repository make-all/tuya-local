from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import AsyncMock, patch

from homeassistant.components.fan import (
    SUPPORT_SET_SPEED,
)

from homeassistant.const import STATE_UNAVAILABLE
from custom_components.tuya_local.generic.fan import TuyaLocalFan
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.generic.switch import TuyaLocalSwitch
from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig

from ..const import DETA_FAN_PAYLOAD
from ..helpers import assert_device_properties_set

SWITCH_DPS = "1"
SPEED_DPS = "3"
LIGHT_DPS = "9"
MASTER_DPS = "101"
TIMER_DPS = "102"
LIGHT_TIMER_DPS = "103"


class TestDetaFan(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        cfg = TuyaDeviceConfig("deta_fan.yaml")
        entities = {}
        entities[cfg.primary_entity.entity] = cfg.primary_entity
        for e in cfg.secondary_entities():
            entities[e.entity] = e

        self.fan_name = (
            "missing" if "fan" not in entities.keys() else entities["fan"].name
        )
        self.light_name = (
            "missing" if "light" not in entities.keys() else entities["light"].name
        )
        self.switch_name = (
            "missing" if "switch" not in entities.keys() else entities["switch"].name
        )
        self.subject = TuyaLocalFan(self.mock_device(), entities.get("fan"))
        self.light = TuyaLocalLight(self.mock_device(), entities.get("light"))
        self.switch = TuyaLocalSwitch(self.mock_device(), entities.get("switch"))
        self.dps = DETA_FAN_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_SET_SPEED,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)
        self.assertTrue(self.light.should_poll)
        self.assertTrue(self.switch.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)
        self.assertEqual(self.light.name, self.subject._device.name)
        self.assertEqual(self.switch.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.fan_name)
        self.assertEqual(self.light.friendly_name, self.light_name)
        self.assertEqual(self.switch.friendly_name, self.switch_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.light.unique_id, self.subject._device.unique_id)
        self.assertEqual(self.switch.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)
        self.assertEqual(self.light.device_info, self.subject._device.device_info)
        self.assertEqual(self.switch.device_info, self.subject._device.device_info)

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

        self.dps[SWITCH_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    def test_speed(self):
        self.dps[SPEED_DPS] = "1"
        self.assertAlmostEqual(self.subject.percentage, 33.3, 1)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 33.3, 1)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(66.7)

    async def test_auto_stringify_speed(self):
        self.dps[SPEED_DPS] = "1"
        self.assertAlmostEqual(self.subject.percentage, 33.3, 1)
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: "2"}):
            await self.subject.async_set_percentage(66.7)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(55)

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.dps[LIGHT_TIMER_DPS] = "6"
        self.assertEqual(self.subject.device_state_attributes, {"timer": 5})
        self.assertEqual(self.light.device_state_attributes, {"timer": 6})

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

    def test_switch_is_on(self):
        self.dps[MASTER_DPS] = True
        self.assertTrue(self.switch.is_on)

        self.dps[MASTER_DPS] = False
        self.assertFalse(self.switch.is_on)

        self.dps[MASTER_DPS] = None
        self.assertEqual(self.switch.is_on, STATE_UNAVAILABLE)

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(
            self.switch._device, {MASTER_DPS: True}
        ):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.light._device, {MASTER_DPS: False}
        ):
            await self.switch.async_turn_off()

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
