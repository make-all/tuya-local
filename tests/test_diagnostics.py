"""Tests for diagnostics platform"""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest.mock import AsyncMock, Mock

from custom_components.tuya_local.const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_TYPE,
)

from custom_components.tuya_local.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
)


async def test_config_entry_diagnostics(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DEVICE_ID: "test_device",
            CONF_LOCAL_KEY: "test_key",
            CONF_TYPE: "simple_switch",
        },
    )
    m_device = AsyncMock()
    hass.data[DOMAIN] = {"test_device": {"device": m_device}}
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag


async def test_device_diagnostics(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DEVICE_ID: "test_device",
            CONF_LOCAL_KEY: "test_key",
            CONF_TYPE: "simple_switch",
        },
    )
    m_device = AsyncMock()
    hass.data[DOMAIN] = {"test_device": {"device": m_device}}
    diag = await async_get_device_diagnostics(hass, entry, m_device)

    assert diag
