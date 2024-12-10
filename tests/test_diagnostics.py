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
