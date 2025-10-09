"""Tests for the light entity."""

from unittest.mock import AsyncMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.climate import TuyaLocalClimate, async_setup_entry
import base64
from custom_components.tuya_local.climate import decode_schedule_base64
from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "heater",
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
    assert type(hass.data[DOMAIN]["dummy"]["climate"]) is TuyaLocalClimate
    m_add_entities.assert_called_once()


# After removal of deprecated entities, there are no secondary climate devices to test against.
# async def test_init_entry_as_secondary(hass):
#     """Test initialisation when climate is a secondary entity"""
#     entry = MockConfigEntry(
#         domain=DOMAIN,
#         data={
#             CONF_TYPE: "goldair_dehumidifier",
#             CONF_DEVICE_ID: "dummy",
#         },
#     )
#     # although async, the async_add_entities function passed to
#     # async_setup_entry is called truly asynchronously. If we use
#     # AsyncMock, it expects us to await the result.
#     m_add_entities = Mock()
#     m_device = AsyncMock()

#     hass.data[DOMAIN] = {}
#     hass.data[DOMAIN]["dummy"] = {}
#     hass.data[DOMAIN]["dummy"]["device"] = m_device

#     await async_setup_entry(hass, entry, m_add_entities)
#     assert (
#         type(hass.data[DOMAIN]["dummy"]["climate_dehumidifier_as_climate"])
#         is TuyaLocalClimate
#     )
#     m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_climate(hass):
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


class TestDecodeScheduleBase64:
    def make_schedule_bytes(self, records):
        """
        Helper to create a bytes object for 18 records, each record is (hour, minute, temp*10 as int, 2 bytes)
        """
        b = bytearray()
        for hour, minute, temp in records:
            b.append(hour)
            b.append(minute)
            temp_int = int(temp * 10)
            b.extend(temp_int.to_bytes(2, "big"))
        return bytes(b)

    def test_decode_schedule_base64_valid(self):
        # 18 records: 6 for each day group, temp increases by 0.5 each
        records = []
        for i in range(18):
            hour = i
            minute = i + 10
            temp = 20.0 + i * 0.5
            records.append((hour, minute, temp))
        raw = self.make_schedule_bytes(records)
        b64 = base64.b64encode(raw).decode()
        schedule = decode_schedule_base64(b64)
        assert schedule is not None
        assert len(schedule) == 3
        assert all(len(day) == 6 for day in schedule)
        # Check first, last, and a middle value
        assert schedule[0][0] == (0, 10, 20.0)
        assert schedule[2][5] == (17, 27, 28.5)
        assert schedule[1][2] == (8, 18, 24.0)

    def test_decode_schedule_base64_invalid_base64(self):
        # Not a valid base64 string
        assert decode_schedule_base64("not_base64!") is None

    def test_decode_schedule_base64_wrong_length(self):
        # Valid base64 but not 72 bytes after decoding
        raw = b"\x00" * 10
        b64 = base64.b64encode(raw).decode()
        assert decode_schedule_base64(b64) is None

    def test_decode_schedule_base64_empty_string(self):
        assert decode_schedule_base64("") is None

    def test_decode_schedule_base64_none_input(self):
        # None is passed
        assert decode_schedule_base64(None) is None

