"""Tests for the humidifier entity."""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest.mock import AsyncMock, Mock

from custom_components.tuya_local.const import (
    CONF_HUMIDIFIER,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_AUTO,
    DOMAIN,
)
from custom_components.tuya_local.generic.humidifier import TuyaLocalHumidifier
from custom_components.tuya_local.humidifier import async_setup_entry


async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TYPE: CONF_TYPE_AUTO, CONF_DEVICE_ID: "dummy"},
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()
    m_device.async_inferred_type = AsyncMock(return_value="dehumidifier")

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"][CONF_HUMIDIFIER]) == TuyaLocalHumidifier
    m_add_entities.assert_called_once()
