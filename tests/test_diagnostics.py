"""Tests for diagnostics platform"""

from unittest.mock import Mock

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
    redact_entity,
)
from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig


@pytest.mark.asyncio
async def test_config_entry_diagnostics(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DEVICE_ID: "test_device",
            CONF_LOCAL_KEY: "test_key",
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "simple_switch",
        },
    )
    m_device = Mock()
    m_device._api_protocol_version_index = 0
    m_device._children = []
    m_device._cached_state = {"1": "Test"}
    m_device._pending_updates = {}
    hass.data[DOMAIN] = {"test_device": {"device": m_device}}
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag


@pytest.mark.asyncio
async def test_device_diagnostics(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DEVICE_ID: "test_device",
            CONF_LOCAL_KEY: "test_key",
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "simple_switch",
        },
    )
    m_device = Mock()
    m_device._api_protocol_version_index = 0
    m_device._children = []
    m_device._cached_state = {"1": "Test"}
    m_device._pending_updates = {}
    hass.data[DOMAIN] = {"test_device": {"device": m_device}}
    diag = await async_get_device_diagnostics(hass, entry, m_device)

    assert diag


@pytest.mark.asyncio
async def test_diagnostic_redaction(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DEVICE_ID: "test_device",
            CONF_LOCAL_KEY: "test_key",
            CONF_PROTOCOL_VERSION: "auto",
            CONF_HOST: "auto",
            CONF_TYPE: "",
        },
    )
    m_device = Mock()
    m_entity = Mock()
    config = TuyaEntityConfig(
        Mock(),
        {
            "entity": "sensor",
            "dps": [
                {
                    "id": "1",
                    "type": "string",
                    "name": "sensor",
                },
                {
                    "id": "2",
                    "type": "string",
                    "name": "secrets",
                    "sensitive": True,
                },
            ],
        },
    )
    m_entity._config = config
    m_device._api_protocol_version_index = 0
    m_device._children = [m_entity]
    m_device._cached_state = {"1": "Test", "2": "secret"}
    m_device._pending_updates = {}
    hass.data[DOMAIN] = {"test_device": {"device": m_device}}
    diag = await async_get_device_diagnostics(hass, entry, m_device)

    assert diag["device_id"] is REDACTED
    assert diag["local_key"] is REDACTED
    assert diag["cached_state"]["2"] is REDACTED


# Deliberately self describing. Realistic looking values get picked up by
# secret scanners, and names containing "secret" or "password" trip ruff's S105.
EXAMPLE_SENSITIVE_VALUE = "example-not-a-real-value"
EXAMPLE_SNAPSHOT = "example-not-real-snapshot-data"


def _device_with_sensitive_dp(dp_name: str, dp_value: str):
    """Build a device with one entity whose dp `dp_name` is sensitive."""
    config = TuyaEntityConfig(
        Mock(),
        {
            "entity": "lock",
            "dps": [
                {"id": "33", "type": "boolean", "name": "lock"},
                {"id": "1", "type": "string", "name": dp_name, "sensitive": True},
            ],
        },
    )
    m_entity = Mock()
    m_entity._config = config
    m_device = Mock()
    m_device.unique_id = "test_device"
    m_device._children = [m_entity]
    m_device.get_property = lambda dp_id: dp_value if dp_id == "1" else None
    return m_device, config.unique_id("test_device")


def test_sensitive_attribute_is_redacted():
    """A sensitive dp published as an extra attribute must be redacted."""
    m_device, unique_id = _device_with_sensitive_dp(
        "unlock_password", EXAMPLE_SENSITIVE_VALUE
    )
    state = {
        "entity_id": "lock.front_door",
        "state": "locked",
        "attributes": {
            "friendly_name": "Front door",
            "unlock_password": EXAMPLE_SENSITIVE_VALUE,
        },
    }

    result = redact_entity(m_device, unique_id, state)

    assert result["attributes"]["unlock_password"] is REDACTED
    assert result["attributes"]["friendly_name"] == "Front door"
    assert EXAMPLE_SENSITIVE_VALUE not in str(result)
    # the entity's own state is not sensitive, so it stays useful
    assert result["state"] == "locked"


def test_sensitive_primary_value_is_redacted():
    """A sensitive dp consumed by the platform surfaces as state, so redact it."""
    m_device, unique_id = _device_with_sensitive_dp("value", EXAMPLE_SENSITIVE_VALUE)
    state = {
        "entity_id": "text.door_code",
        "state": EXAMPLE_SENSITIVE_VALUE,
        "attributes": {"friendly_name": "Door code"},
    }

    result = redact_entity(m_device, unique_id, state)

    assert result["state"] is REDACTED
    assert EXAMPLE_SENSITIVE_VALUE not in str(result)


def test_state_kept_when_sensitive_dp_is_not_the_state():
    """A camera's snapshot is sensitive, but its state is not - keep the state."""
    m_device, unique_id = _device_with_sensitive_dp("snapshot", EXAMPLE_SNAPSHOT)
    state = {
        "entity_id": "camera.doorbell",
        "state": "recording",
        "attributes": {"friendly_name": "Doorbell"},
    }

    result = redact_entity(m_device, unique_id, state)

    assert result["state"] == "recording"
    assert EXAMPLE_SNAPSHOT not in str(result)


def test_unrelated_entity_state_is_untouched():
    """An entity with no sensitive dps is returned unchanged."""
    m_device, _ = _device_with_sensitive_dp("unlock_password", EXAMPLE_SENSITIVE_VALUE)
    state = {"entity_id": "lock.other", "state": "locked", "attributes": {}}

    assert redact_entity(m_device, "some-other-unique-id", state) == state
