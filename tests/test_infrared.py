"""Tests for the infrared entity."""

import pytest
from infrared_protocols.commands import NECCommand
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig
from custom_components.tuya_local.infrared import TuyaLocalInfrared, async_setup_entry

from .helpers import assert_device_properties_set, mock_device


@pytest.mark.asyncio
async def test_init_entry(hass, mocker):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "ir_remote_sensors",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = mocker.Mock()
    m_device = mocker.AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["infrared"]) is TuyaLocalInfrared
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_infrared(hass, mocker):
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
    m_add_entities = mocker.Mock()
    m_device = mocker.AsyncMock()

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
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = mocker.Mock()
    m_device = mocker.AsyncMock()

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
async def test_async_send_command(mocker):
    """Test that infrared encodes commands as expected."""
    config = {
        "entity": "infrared",
        "dps": [
            {
                "id": "201",
                "name": "send",
                "type": "base64",
            }
        ],
    }
    tuyadevice = mocker.MagicMock()
    dps = {"201": ""}
    device = mock_device(dps, mocker)
    infrared = TuyaLocalInfrared(
        device,
        TuyaEntityConfig(tuyadevice, config),
    )

    async with assert_device_properties_set(
        device,
        {
            "201": (
                '{"control": "send_ir", "type": 0, "head": "", "key1": "1KCOUETICMgIyAjI'
                "CMgKXBjICMgIyAjICMgIyAjICMgIyApcGMgIyAjIClwYyAjICMgIyAjIClwYyAjICMgKXBj"
                "ICMgIyAjICMgKXBjICMgIyAjICMgKXBjIClwYyAjICMgIyAjIClwYyAjICMgKXBjIClwYyA"
                'jICMgIyAjIClwYyApcGMgKIEw=="}'
            )
        },
    ):
        await infrared.async_send_command(
            NECCommand(address=0x5284, command=0x32, modulation=38000)
        )
