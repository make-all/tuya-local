"""Tests for the lock entity."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest.mock import AsyncMock

from custom_components.tuya_local.const import (
    CONF_CHILD_LOCK,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_AUTO,
    CONF_TYPE_GPPH_HEATER,
    DOMAIN,
)
from custom_components.tuya_local.heater.lock import GoldairHeaterChildLock
from custom_components.tuya_local.lock import async_setup_entry


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_TYPE: CONF_TYPE_AUTO, CONF_DEVICE_ID: "dummy"},
    )
    m_add_entities = AsyncMock()
    m_device = AsyncMock()
    m_device.async_inferred_type = AsyncMock(return_value=CONF_TYPE_GPPH_HEATER)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"][CONF_CHILD_LOCK]) == GoldairHeaterChildLock
    m_add_entities.assert_called_once()
