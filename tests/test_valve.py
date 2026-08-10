"""Tests for the valve entity"""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.valve import (
    ValveEntityFeature,
    ValveState,
)
from homeassistant.components.valve.const import ValveEntityStateAttribute
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.helpers.device_config import get_config
from custom_components.tuya_local.valve import TuyaLocalValve, async_setup_entry

from .helpers import assert_device_properties_set, mock_device

FRANKEVER_DPS = {
    "1": True,
    "9": 0,
    "38": "memory",
    "101": 100,
    "102": 100,
}


def _make_frankever_valve(mocker, dps=None):
    """Create a valve using the FrankEver position-controlled profile."""
    config = get_config("frankever_watervalve")
    entity_config = next(
        entity for entity in config.all_entities() if entity.entity == "valve"
    )
    device = mock_device(dps or FRANKEVER_DPS, mocker)
    return TuyaLocalValve(device, entity_config), device


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test initialisation"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "ble_water_valve",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {
            "device": m_device,
        },
    }
    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["valve_water"]) is TuyaLocalValve
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_valve(hass):
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

    hass.data[DOMAIN] = {
        "dummy": {
            "device": m_device,
        },
    }
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.parametrize(
    ("position", "expected_state"),
    [
        (0, ValveState.CLOSED),
        (20, ValveState.OPEN),
        (100, ValveState.OPEN),
    ],
)
def test_separate_current_position(mocker, position, expected_state):
    """Current position is reported by the read-only feedback DP."""
    dps = {**FRANKEVER_DPS, "101": position, "102": position}
    valve, _ = _make_frankever_valve(mocker, dps)

    assert valve.current_valve_position == position
    assert valve.is_closed is (position == 0)
    assert valve.state == expected_state
    assert valve.state_attributes == {
        ValveEntityStateAttribute.IS_CLOSED: position == 0,
        ValveEntityStateAttribute.CURRENT_POSITION: position,
    }
    assert valve.supported_features == (
        ValveEntityFeature.OPEN
        | ValveEntityFeature.CLOSE
        | ValveEntityFeature.SET_POSITION
    )


@pytest.mark.asyncio
async def test_set_position_writes_target_only(mocker):
    """Setting a target position does not change the separate switch."""
    valve, device = _make_frankever_valve(mocker)

    async with assert_device_properties_set(device, {"101": 50}):
        await valve.async_set_valve_position(50)


@pytest.mark.asyncio
async def test_set_zero_writes_target_only(mocker):
    """Setting a zero target position does not change the separate switch."""
    valve, device = _make_frankever_valve(mocker)

    async with assert_device_properties_set(device, {"101": 0}):
        await valve.async_set_valve_position(0)


@pytest.mark.asyncio
async def test_open_uses_switch(mocker):
    """Opening uses the switch without changing a non-zero target position."""
    valve, device = _make_frankever_valve(mocker)

    async with assert_device_properties_set(device, {"1": True}):
        await valve.async_open_valve()


@pytest.mark.asyncio
async def test_close_uses_switch(mocker):
    """Closing uses the switch without changing the target position."""
    valve, device = _make_frankever_valve(mocker)

    async with assert_device_properties_set(device, {"1": False}):
        await valve.async_close_valve()


def test_frankever_product_match_is_preferred():
    """The explicit product match is stronger than the Tellur DPS match."""
    frankever = get_config("frankever_watervalve")
    tellur = get_config("tellur_tll331501_watervalve")
    product_ids = ["nzx0kku9d6eq59nt"]

    assert frankever.matches_product(product_ids[0])
    assert frankever.match_quality(FRANKEVER_DPS, product_ids) == 101
    assert tellur.match_quality(FRANKEVER_DPS) == 100


def test_frankever_auxiliary_entity_values(mocker):
    """Countdown and initial-state mappings retain their observed values."""
    config = get_config("frankever_watervalve")
    entities = {entity.entity: entity for entity in config.all_entities()}
    device = mock_device(FRANKEVER_DPS, mocker)

    assert entities["time"].find_dps("second").get_value(device) == 0
    initial_state = entities["select"].find_dps("option")
    assert initial_state.get_value(device) == "memory"
    assert initial_state.values(device) == ["off", "on", "memory"]


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
