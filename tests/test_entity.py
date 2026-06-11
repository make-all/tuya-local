"""Tests for the TuyaLocalEntity base class and unit_from_ascii helper."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    UnitOfArea,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from custom_components.tuya_local.entity import (
    BLACKLISTED_ATTRIBUTES,
    TuyaLocalEntity,
    unit_from_ascii,
)


class DummySuper:
    """Simulates a HA entity base with a name and icon property."""

    @property
    def name(self):
        return "translated_name"

    @property
    def icon(self):
        return "mdi:default-icon"


class DummyEntity(TuyaLocalEntity, DummySuper):
    """Concrete subclass so we can instantiate TuyaLocalEntity."""

    def _default_to_device_class_name(self):
        return False


@pytest.fixture
def mock_device():
    device = MagicMock()
    device.has_returned_state = True
    device.unique_id = "test_device_123"
    device.name = "Test Device"
    device.device_info = {"identifiers": {("tuya_local", "test_device_123")}}
    device.register_entity = MagicMock()
    device.async_unregister_entity = AsyncMock()
    device.async_refresh = AsyncMock()
    return device


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.name = "Test Entity"
    config.translation_key = None
    config.translation_only_key = None
    config.translation_placeholders = None
    config.entity_category = None
    config.deprecated = False
    config.deprecation_message = ""
    config.config_id = "test_config"
    config.device_class = None

    dp1 = MagicMock()
    dp1.name = "state"
    dp1.hidden = False
    dp1.optional = False
    dp1.get_value.return_value = "on"

    dp2 = MagicMock()
    dp2.name = "temperature"
    dp2.hidden = False
    dp2.optional = False
    dp2.get_value.return_value = 25

    dp3 = MagicMock()
    dp3.name = "available"
    dp3.hidden = False
    dp3.optional = False
    dp3.get_value.return_value = True

    config.dps.return_value = [dp1, dp2, dp3]
    config.icon.return_value = None
    config.available.return_value = True
    config.unique_id.return_value = "tuya_local_test_device_123_test"
    config.enabled_by_default.return_value = True

    return config


@pytest.fixture
def entity(mock_device, mock_config):
    e = DummyEntity()
    dps = e._init_begin(mock_device, mock_config)
    e._init_end(dps)
    return e


class TestInitBeginEnd:
    def test_init_begin_sets_device_and_config(self, mock_device, mock_config):
        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        assert e._device is mock_device
        assert e._config is mock_config
        assert isinstance(dps, dict)

    def test_init_begin_returns_dps_dict(self, mock_device, mock_config):
        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        assert "state" in dps
        assert "temperature" in dps
        assert "available" in dps

    def test_init_begin_with_translation_key(self, mock_device, mock_config):
        mock_config.translation_key = "my_key"
        e = DummyEntity()
        e._init_begin(mock_device, mock_config)
        assert e._attr_translation_key == "my_key"

    def test_init_begin_with_translation_only_key(self, mock_device, mock_config):
        mock_config.translation_key = None
        mock_config.translation_only_key = "only_key"
        e = DummyEntity()
        e._init_begin(mock_device, mock_config)
        assert e._attr_translation_key == "only_key"

    def test_init_begin_with_placeholders(self, mock_device, mock_config):
        mock_config.translation_placeholders = {"x": "1"}
        e = DummyEntity()
        e._init_begin(mock_device, mock_config)
        assert e._attr_translation_placeholders == {"x": "1"}

    def test_init_end_excludes_blacklisted(self, mock_device, mock_config):
        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        e._init_end(dps)
        attr_names = [d.name for d in e._attr_dps]
        for bl in BLACKLISTED_ATTRIBUTES:
            assert bl not in attr_names

    def test_init_end_excludes_hidden(self, mock_device, mock_config):
        dp = MagicMock()
        dp.name = "visible"
        dp.hidden = True
        dp.optional = False
        mock_config.dps.return_value = [dp]

        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        e._init_end(dps)
        assert len(e._attr_dps) == 0

    def test_init_end_includes_non_blacklisted_non_hidden(
        self, mock_device, mock_config
    ):
        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        e._init_end(dps)
        attr_names = [d.name for d in e._attr_dps]
        assert "temperature" in attr_names


class TestProperties:
    def test_should_poll(self, entity):
        assert entity.should_poll is False

    def test_available_when_device_returned_state(self, entity):
        assert entity.available is True

    def test_available_false_when_no_state(self, entity, mock_device):
        mock_device.has_returned_state = False
        assert entity.available is False

    def test_available_false_when_config_unavailable(self, entity, mock_config):
        mock_config.available.return_value = False
        assert entity.available is False

    def test_has_entity_name(self, entity):
        assert entity.has_entity_name is True

    def test_name_returns_config_name(self, entity):
        assert entity.name == "Test Entity"

    def test_name_falls_back_to_super(self, entity, mock_config):
        mock_config.name = None
        mock_config.translation_key = "some_key"
        # When use_device_name is False (has translation_key), name calls super
        assert entity.name is not None

    def test_name_uses_device_name_when_no_own_name(self, entity, mock_config):
        mock_config.name = None
        mock_config.translation_key = None
        mock_config.device_class = None
        assert entity.use_device_name is True

    def test_use_device_name_false_with_name(self, entity):
        assert entity.use_device_name is False

    def test_use_device_name_false_with_translation_key(self, entity, mock_config):
        mock_config.name = None
        mock_config.translation_key = "some_key"
        assert entity.use_device_name is False

    def test_unique_id(self, entity):
        assert entity.unique_id == "tuya_local_test_device_123_test"

    def test_device_info(self, entity, mock_device):
        assert entity.device_info is mock_device.device_info

    def test_entity_category_none(self, entity):
        assert entity.entity_category is None

    def test_entity_category_config(self, entity, mock_config):
        mock_config.entity_category = "config"
        assert entity.entity_category == EntityCategory.CONFIG

    def test_entity_category_diagnostic(self, entity, mock_config):
        mock_config.entity_category = "diagnostic"
        assert entity.entity_category == EntityCategory.DIAGNOSTIC

    def test_icon_from_config(self, entity, mock_config):
        mock_config.icon.return_value = "mdi:custom-icon"
        assert entity.icon == "mdi:custom-icon"

    def test_icon_falls_back_to_super(self, entity, mock_config):
        mock_config.icon.return_value = None
        assert entity.icon == "mdi:default-icon"

    def test_extra_state_attributes(self, entity):
        attrs = entity.extra_state_attributes
        assert "temperature" in attrs
        assert attrs["temperature"] == 25

    def test_extra_state_attributes_skips_none_optional(self, mock_device, mock_config):
        dp = MagicMock()
        dp.name = "opt_attr"
        dp.hidden = False
        dp.optional = True
        dp.get_value.return_value = None
        mock_config.dps.return_value = [dp]

        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        e._init_end(dps)
        attrs = e.extra_state_attributes
        assert "opt_attr" not in attrs

    def test_extra_state_attributes_includes_none_required(
        self, mock_device, mock_config
    ):
        dp = MagicMock()
        dp.name = "req_attr"
        dp.hidden = False
        dp.optional = False
        dp.get_value.return_value = None
        mock_config.dps.return_value = [dp]

        e = DummyEntity()
        dps = e._init_begin(mock_device, mock_config)
        e._init_end(dps)
        attrs = e.extra_state_attributes
        assert "req_attr" in attrs
        assert attrs["req_attr"] is None

    def test_entity_registry_enabled_default(self, entity, mock_config):
        assert entity.entity_registry_enabled_default is True
        mock_config.enabled_by_default.return_value = False
        assert entity.entity_registry_enabled_default is False


class TestAsyncMethods:
    @pytest.mark.asyncio
    async def test_async_update(self, entity, mock_device):
        await entity.async_update()
        mock_device.async_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, entity, mock_device):
        await entity.async_added_to_hass()
        mock_device.register_entity.assert_called_once_with(entity)

    @pytest.mark.asyncio
    async def test_async_added_to_hass_logs_deprecation(
        self, entity, mock_device, mock_config
    ):
        mock_config.deprecated = True
        mock_config.deprecation_message = "This entity is deprecated"
        with patch("custom_components.tuya_local.entity._LOGGER") as mock_logger:
            await entity.async_added_to_hass()
            mock_logger.warning.assert_called_with("This entity is deprecated")

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass(self, entity, mock_device):
        await entity.async_will_remove_from_hass()
        mock_device.async_unregister_entity.assert_awaited_once_with(entity)

    def test_on_receive_does_nothing(self, entity):
        # Default implementation is a no-op
        entity.on_receive({}, False)


class TestUnitFromAscii:
    def test_celsius(self):
        assert unit_from_ascii("C") == UnitOfTemperature.CELSIUS.value

    def test_fahrenheit(self):
        assert unit_from_ascii("F") == UnitOfTemperature.FAHRENHEIT.value

    def test_micrograms(self):
        assert unit_from_ascii("ugm3") == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

    def test_square_meters(self):
        assert unit_from_ascii("m2") == UnitOfArea.SQUARE_METERS

    def test_passthrough_unknown(self):
        assert unit_from_ascii("km/h") == "km/h"

    def test_passthrough_empty(self):
        assert unit_from_ascii("") == ""
