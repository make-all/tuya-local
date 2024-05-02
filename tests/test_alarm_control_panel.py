"""Tests for the alarm_control_panel entity."""

from unittest.mock import AsyncMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.alarm_control_panel import (
    TuyaLocalAlarmControlPanel,
    async_setup_entry,
)
from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test initialisation"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "zx_g30_alarm",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}

    await async_setup_entry(hass, entry, m_add_entities)
    assert (
        type(hass.data[DOMAIN]["dummy"]["alarm_control_panel"])
        == TuyaLocalAlarmControlPanel
    )
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_as_secondary(hass):
    """Test initialisation when alarm_control_panel is a secondary entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "zx_db11_doorbell_alarm",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}

    await async_setup_entry(hass, entry, m_add_entities)
    assert (
        type(hass.data[DOMAIN]["dummy"]["alarm_control_panel_alarm"])
        == TuyaLocalAlarmControlPanel
    )
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_alarm_control_panel(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "kogan_heater",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_init_entry_fails_if_config_is_missing(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "non_existing",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()
