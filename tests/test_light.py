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


@pytest.mark.asyncio
async def test_async_turn_on_with_brightness_on_packed_dp():
    """Switch-on must merge cleanly when the dp is shared across sub-fields.

    On packed dps where switch / brightness / color all share the same dp id
    (e.g. dp 51 with different masks), the switch-on branch was previously
    skipped once the brightness branch had populated `settings[dp_id]`,
    leaving the bulb with brightness staged but not actually on.

    For masked switch dps, the merge is always safe — `get_values_to_set`
    with `pending_map=settings` ORs onto the existing pending value — so the
    final write contains the switch byte AND the brightness bytes.
    """
    mock_device = AsyncMock()
    mock_device.get_property = Mock()
    # Bulb currently off: switch byte (mask 0001) is 0, brightness is 0.
    dps = {"1": "000000000000"}
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
                    "type": "hex",
                    "mask": "000100000000",
                },
                {
                    "id": "1",
                    "name": "brightness",
                    "type": "hex",
                    "mask": "0000FFFF0000",
                    "range": {"min": 0, "max": 1000},
                },
            ],
        },
    )
    light = TuyaLocalLight(mock_device, config)
    await light.async_turn_on(brightness=255)
    mock_device.async_set_properties.assert_called_once()
    sent = mock_device.async_set_properties.call_args[0][0]
    sent_value = int(sent["1"], 16)
    # brightness bytes set
    assert sent_value & 0x0000FFFF0000 != 0
    # switch byte also set (this is the bug — was zero before the fix)
    assert sent_value & 0x000100000000 != 0


@pytest.mark.asyncio
async def test_is_off_when_off_by_brightness():
    """Test that the light appears off when turned off by brightness."""
    mock_device = AsyncMock()
    mock_device.get_property = Mock()
    dps = {"1": 0}
    mock_device.get_property.side_effect = lambda arg: dps[arg]
    mock_config = Mock()
    config = TuyaEntityConfig(
        mock_config,
        {
            "entity": "light",
            "dps": [
                {
                    "id": "1",
                    "name": "brightness",
                    "type": "integer",
                    "range": {"min": 0, "max": 100},
                },
            ],
        },
    )
    light = TuyaLocalLight(mock_device, config)
    assert light.is_on is False
    assert light.brightness == 0
