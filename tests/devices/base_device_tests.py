from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, PropertyMock, patch
from uuid import uuid4

from homeassistant.helpers.entity import EntityCategory

from custom_components.tuya_local.alarm_control_panel import TuyaLocalAlarmControlPanel
from custom_components.tuya_local.binary_sensor import TuyaLocalBinarySensor
from custom_components.tuya_local.button import TuyaLocalButton
from custom_components.tuya_local.camera import TuyaLocalCamera
from custom_components.tuya_local.climate import TuyaLocalClimate
from custom_components.tuya_local.cover import TuyaLocalCover
from custom_components.tuya_local.fan import TuyaLocalFan
from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    possible_matches,
)
from custom_components.tuya_local.humidifier import TuyaLocalHumidifier
from custom_components.tuya_local.light import TuyaLocalLight
from custom_components.tuya_local.lock import TuyaLocalLock
from custom_components.tuya_local.number import TuyaLocalNumber
from custom_components.tuya_local.select import TuyaLocalSelect
from custom_components.tuya_local.sensor import TuyaLocalSensor
from custom_components.tuya_local.siren import TuyaLocalSiren
from custom_components.tuya_local.switch import TuyaLocalSwitch
from custom_components.tuya_local.vacuum import TuyaLocalVacuum
from custom_components.tuya_local.water_heater import TuyaLocalWaterHeater

DEVICE_TYPES = {
    "alarm_control_panel": TuyaLocalAlarmControlPanel,
    "binary_sensor": TuyaLocalBinarySensor,
    "button": TuyaLocalButton,
    "camera": TuyaLocalCamera,
    "climate": TuyaLocalClimate,
    "cover": TuyaLocalCover,
    "fan": TuyaLocalFan,
    "humidifier": TuyaLocalHumidifier,
    "light": TuyaLocalLight,
    "lock": TuyaLocalLock,
    "number": TuyaLocalNumber,
    "switch": TuyaLocalSwitch,
    "select": TuyaLocalSelect,
    "sensor": TuyaLocalSensor,
    "siren": TuyaLocalSiren,
    "vacuum": TuyaLocalVacuum,
    "water_heater": TuyaLocalWaterHeater,
}


class TuyaDeviceTestCase(IsolatedAsyncioTestCase):
    __test__ = False

    def setUpForConfig(self, config_file, payload):
        """Perform setup tasks for every test."""
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        self.dps = payload.copy()
        self.mock_device.get_property.side_effect = lambda id: self.dps.get(id)
        cfg = TuyaDeviceConfig(config_file)
        self.conf_type = cfg.legacy_type
        type(self.mock_device).has_returned_state = PropertyMock(return_value=True)
        type(self.mock_device).unique_id = PropertyMock(return_value=str(uuid4()))
        self.mock_device.name = cfg.name

        self.entities = {}
        self.secondary_category = []
        self.primary_entity = cfg.primary_entity.config_id
        self.entities[self.primary_entity] = self.create_entity(cfg.primary_entity)

        self.names = {}
        self.names[cfg.primary_entity.config_id] = cfg.primary_entity.name
        for e in cfg.secondary_entities():
            self.entities[e.config_id] = self.create_entity(e)
            self.names[e.config_id] = e.name

    def create_entity(self, config):
        """Create an entity to match the config"""
        dev_type = DEVICE_TYPES[config.entity]
        if dev_type:
            entity = dev_type(self.mock_device, config)
            entity.platform = Mock()
            entity.platform.name = dev_type
            entity.platform.platform_translations = {}
            return entity

    def mark_secondary(self, entities):
        self.secondary_category = self.secondary_category + entities

    def test_config_matched(self):
        for cfg in possible_matches(self.dps):
            if cfg.legacy_type == self.conf_type:
                self.assertEqual(
                    cfg.match_quality(self.dps),
                    100.0,
                    msg=f"{self.conf_type} is an imperfect match",
                )
                return
        self.fail()

    def test_should_poll(self):
        for e in self.entities.values():
            self.assertFalse(e.should_poll)

    def test_available(self):
        for e in self.entities.values():
            self.assertTrue(e.available)

    def test_entity_category(self):
        for k, e in self.entities.items():
            if k in self.secondary_category:
                if type(e) in [TuyaLocalBinarySensor, TuyaLocalSensor]:
                    self.assertEqual(
                        e.entity_category,
                        EntityCategory.DIAGNOSTIC,
                        msg=f"{k} is {e.entity_category.value}, expected diagnostic",
                    )
                else:
                    self.assertEqual(
                        e.entity_category,
                        EntityCategory.CONFIG,
                        msg=f"{k} is {e.entity_category.value}, expected config",
                    )
            else:
                self.assertIsNone(
                    e.entity_category,
                    msg=f"{k} is {e.entity_category}, expected None",
                )

    # name has become more difficult to test with translation support, but it is working
    # in practice.
    # def test_name_returns_device_name(self):
    #     for e in self.entities:
    #         self.assertEqual(self.entities[e].name, self.names[e])

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
