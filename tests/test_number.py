"""Tests for the number entity."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig
from custom_components.tuya_local.number import TuyaLocalNumber, async_setup_entry

from .helpers import assert_device_properties_set, mock_device


@pytest.mark.asyncio
async def test_init_entry(hass, mocker):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "anko_fan",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = mocker.Mock()
    m_device = mocker.AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {"device": m_device},
    }

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["number_timer"]) is TuyaLocalNumber
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_number(hass, mocker):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "simple_switch",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = mocker.Mock()
    m_device = mocker.AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {"device": m_device},
    }
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_init_entry_fails_if_config_is_missing(hass, mocker):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "non_existing",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = mocker.Mock()
    m_device = mocker.AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {"device": m_device},
    }
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


def test_decimal(mocker):
    """Test the decimal property."""
    config = {
        "entity": "number",
        "dps": [
            {
                "id": "1",
                "type": "integer",
                "name": "value",
                "range": {
                    "min": 0,
                    "max": 100,
                },
            },
            {
                "id": "2",
                "type": "integer",
                "name": "decimal",
                "mapping": [
                    {
                        "scale": 10,
                    }
                ],
                "range": {
                    "min": 0,
                    "max": 9,
                },
            },
        ],
    }
    tuyadevice = mocker.AsyncMock()
    dps = {"1": 12, "2": 3}
    device = mock_device(dps, mocker)
    number = TuyaLocalNumber(device, TuyaEntityConfig(tuyadevice, config))
    assert number.native_value == 12.3


@pytest.mark.asyncio
async def test_set_decimal(mocker):
    """Test the decimal property."""
    config = {
        "entity": "number",
        "dps": [
            {
                "id": "1",
                "type": "integer",
                "name": "value",
                "range": {
                    "min": 0,
                    "max": 100,
                },
            },
            {
                "id": "2",
                "type": "integer",
                "name": "decimal",
                "mapping": [
                    {
                        "scale": 10,
                    }
                ],
                "range": {
                    "min": 0,
                    "max": 9,
                },
            },
        ],
    }
    tuyadevice = mocker.AsyncMock()
    dps = {"1": 1, "2": 1}
    device = mock_device(dps, mocker)
    number = TuyaLocalNumber(device, TuyaEntityConfig(tuyadevice, config))

    async with assert_device_properties_set(
        device,
        {"1": 10, "2": 5},
    ):
        await number.async_set_native_value(10.5)
