"""Tests for the media_player entity."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.media_player import MediaPlayerState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.media_player import (
    TuyaLocalMediaPlayer,
    async_setup_entry,
)

from .helpers import mock_device


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "ekaza_minipad_controlpanel",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}

    await async_setup_entry(hass, entry, m_add_entities)
    assert (
        type(hass.data[DOMAIN]["dummy"]["media_player_speaker"]) is TuyaLocalMediaPlayer
    )
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_media_player(hass):
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

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False, "Expected async_setup_entry to raise a ValueError"
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

    hass.data[DOMAIN] = {"dummy": {"device": m_device}}
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False, "Expected async_setup_entry to raise a ValueError"
    except ValueError:
        pass
    m_add_entities.assert_not_called()


# Most features are simple mappings to dps values, but state can be more complex
class TestMediaPlayerState:
    """Test the state property of the media_player entity."""

    @pytest.mark.asyncio
    async def async_test_state(self, hass, mocker):
        """Test the state property."""
        dps = {"82": True}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_TYPE: "ekaza_minipad_controlpanel",
                CONF_DEVICE_ID: "dummy",
                CONF_PROTOCOL_VERSION: "auto",
            },
        )
        m_add_entities = Mock()
        m_device = mock_device(dps, mocker)

        hass.data[DOMAIN] = {"dummy": {"device": m_device}}

        await async_setup_entry(hass, entry, m_add_entities)
        media_player = hass.data[DOMAIN]["dummy"]["media_player_speaker"]

        # Test that the state is correct when the device is playing
        assert media_player.state == MediaPlayerState.PLAYING
