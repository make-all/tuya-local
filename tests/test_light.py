"""Tests for the light entity."""

from unittest.mock import AsyncMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig
from custom_components.tuya_local.light import TuyaLocalLight, async_setup_entry


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "goldair_gpph_heater",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["light_display"]) is TuyaLocalLight
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_light(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "smartplugv1",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
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
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_async_turn_on_with_white_param():
    """Test using WHITE param for async_turn_on."""
    mock_device = AsyncMock()
    mock_device.get_property = Mock()
    dps = {"1": True, "2": "colour", "3": 1000, "4": "ABCDEFFF"}
    mock_device.get_property.side_effect = lambda arg: dps[arg]
    mock_config = Mock()
    config = TuyaEntityConfig(
        mock_config,
        {
            "entity": "light",
            "dps": [
                {
                    "id": "1",
                    "name": "switch",
                    "type": "boolean",
                },
                {
                    "id": "2",
                    "name": "color_mode",
                    "type": "string",
                    "mapping": [
                        {
                            "dps_val": "white",
                            "value": "white",
                        },
                        {
                            "dps_val": "colour",
                            "value": "hs",
                        },
                    ],
                },
                {
                    "id": "3",
                    "name": "brightness",
                    "type": "integer",
                    "range": {
                        "min": 10,
                        "max": 1000,
                    },
                },
                {
                    "id": "4",
                    "name": "hs",
                    "type": "hex",
                },
            ],
        },
    )
    light = TuyaLocalLight(mock_device, config)
    await light.async_turn_on(white=128)
    mock_device.async_set_properties.assert_called_once_with({"2": "white", "3": 506})
