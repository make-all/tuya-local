"""Tests for diagnostics platform"""

from unittest.mock import AsyncMock

import pytest
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
    m_device = AsyncMock()
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
    m_device = AsyncMock()
    hass.data[DOMAIN] = {"test_device": {"device": m_device}}
    diag = await async_get_device_diagnostics(hass, entry, m_device)

    assert diag
