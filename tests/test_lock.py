"""Tests for the lock entity."""

from base64 import b64encode
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_BLE_UNLOCK_CHECK,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.device import setup_device
from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig
from custom_components.tuya_local.lock import TuyaLocalLock, async_setup_entry

BLE_UNLOCK_CHECK = b64encode(bytes(range(1, 20))).decode("utf-8")
BLE_UNLOCK_TIME = 0x01020304
BLE_UNLOCK_MSG = b64encode(
    bytes(
        [
            0x03,
            0x04,
            0x01,
            0x02,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x01,
            0x01,
            0x02,
            0x03,
            0x04,
            0x00,
            0x01,
        ]
    )
).decode("utf-8")


def make_lock(dps, ble_unlock_check=BLE_UNLOCK_CHECK):
    """Create a TuyaLocalLock with a mocked device."""
    device = Mock()
    device.name = "Test"
    device.unique_id = "test"
    device.has_returned_state = True
    device.ble_unlock_check = ble_unlock_check
    device.get_property.return_value = None
    device.async_set_properties = AsyncMock()
    config = TuyaEntityConfig(Mock(), {"entity": "lock", "dps": dps})
    return TuyaLocalLock(device, config), device


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
    assert type(hass.data[DOMAIN]["dummy"]["lock_child_lock"]) is TuyaLocalLock
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_lock(hass):
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


def test_build_ble_unlock_msg():
    """Test building an authenticated BLE unlock payload."""
    lock, _device = make_lock([])

    assert (
        lock.build_ble_unlock_msg(BLE_UNLOCK_CHECK, BLE_UNLOCK_TIME) == BLE_UNLOCK_MSG
    )


def test_build_ble_unlock_msg_rejects_invalid_base64():
    """Test authenticated BLE unlock rejects invalid base64."""
    lock, _device = make_lock([])

    with pytest.raises(HomeAssistantError):
        lock.build_ble_unlock_msg("not base64", BLE_UNLOCK_TIME)


def test_build_ble_unlock_msg_rejects_wrong_length():
    """Test authenticated BLE unlock source must decode to 19 bytes."""
    lock, _device = make_lock([])

    with pytest.raises(HomeAssistantError):
        lock.build_ble_unlock_msg(
            b64encode(b"too short").decode("utf-8"), BLE_UNLOCK_TIME
        )


@pytest.mark.asyncio
async def test_authenticated_ble_unlock_takes_precedence_over_lock_dp(mocker):
    """Test authenticated BLE unlock avoids writing false to the lock dp."""
    mocker.patch("custom_components.tuya_local.lock.time", return_value=BLE_UNLOCK_TIME)
    lock, device = make_lock(
        [
            {"id": 46, "type": "boolean", "name": "lock"},
            {"id": 71, "type": "string", "name": "authenticated_ble_unlock"},
        ]
    )

    await lock.async_unlock()

    device.async_set_properties.assert_awaited_once_with({"71": BLE_UNLOCK_MSG})


@pytest.mark.asyncio
async def test_passive_ble_unlock_check_behavior_is_unchanged():
    """Test passive ble_unlock_check does not opt in to authenticated unlock."""
    lock, device = make_lock(
        [
            {"id": 46, "type": "boolean", "name": "lock"},
            {"id": 71, "type": "string", "name": "ble_unlock_check"},
        ]
    )

    await lock.async_unlock()

    device.async_set_properties.assert_awaited_once_with({"46": False})


@pytest.mark.asyncio
async def test_authenticated_ble_unlock_requires_configured_source():
    """Test missing configured BLE unlock source sends no command."""
    lock, device = make_lock(
        [
            {"id": 46, "type": "boolean", "name": "lock"},
            {"id": 71, "type": "string", "name": "authenticated_ble_unlock"},
        ],
        ble_unlock_check=None,
    )

    with pytest.raises(HomeAssistantError):
        await lock.async_unlock()

    device.async_set_properties.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "ble_unlock_check",
    [
        "not base64",
        b64encode(b"too short").decode("utf-8"),
    ],
)
async def test_authenticated_ble_unlock_rejects_invalid_configured_source(
    ble_unlock_check,
):
    """Test invalid configured BLE unlock source sends no command."""
    lock, device = make_lock(
        [
            {"id": 46, "type": "boolean", "name": "lock"},
            {"id": 71, "type": "string", "name": "authenticated_ble_unlock"},
        ],
        ble_unlock_check=ble_unlock_check,
    )

    with pytest.raises(HomeAssistantError):
        await lock.async_unlock()

    device.async_set_properties.assert_not_awaited()


def test_setup_device_stores_ble_unlock_check(hass, mocker):
    """Test setup_device passes BLE unlock source to the runtime device."""
    api = mocker.MagicMock()
    api.parent = None
    api.id = "deviceid"
    mocker.patch(
        "custom_components.tuya_local.device.tinytuya.Device", return_value=api
    )

    device = setup_device(
        hass,
        {
            CONF_NAME: "Test",
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_PROTOCOL_VERSION: 3.4,
            CONF_TYPE: "test",
            CONF_POLL_ONLY: False,
            CONF_BLE_UNLOCK_CHECK: BLE_UNLOCK_CHECK,
        },
    )

    assert device.ble_unlock_check == BLE_UNLOCK_CHECK


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
