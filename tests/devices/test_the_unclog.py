"""Tests for The Unclog using the current config and entity test helpers."""

import pytest

from custom_components.tuya_local.binary_sensor import TuyaLocalBinarySensor
from custom_components.tuya_local.helpers.device_config import get_config
from custom_components.tuya_local.select import TuyaLocalSelect
from custom_components.tuya_local.switch import TuyaLocalSwitch
from tests.const import THE_UNCLOG_PAYLOAD
from tests.helpers import assert_device_properties_set, mock_device


def test_config_and_sample(mocker):
    """The live payload matches and initializes all four expected entities."""
    config = get_config("the_unclog")
    assert config.matches(THE_UNCLOG_PAYLOAD, [])
    assert config.matches(THE_UNCLOG_PAYLOAD, ["ir6qiyn5s0pbnbz7"])
    assert config.matches_product("ir6qiyn5s0pbnbz7")
    entities = list(config.all_entities())
    assert [
        (entity.entity, entity.name, entity.entity_category) for entity in entities
    ] == [
        ("switch", None, None),
        ("select", "Frequency", "config"),
        ("select", "Duration", "config"),
        ("binary_sensor", "Status", "diagnostic"),
    ]
    assert [
        [(dp.id, dp.name, dp.type) for dp in entity.dps()] for entity in entities
    ] == [
        [("1", "switch", bool)],
        [("101", "option", str)],
        [("103", "option", str)],
        [("102", "sensor", bool)],
    ]
    device = mock_device(THE_UNCLOG_PAYLOAD, mocker)
    assert TuyaLocalSwitch(device, entities[0]).is_on is False
    assert TuyaLocalSelect(device, entities[1]).current_option == "Every 3 Days"
    assert TuyaLocalSelect(device, entities[2]).current_option == "15 s"
    assert TuyaLocalBinarySensor(device, entities[3]).is_on is True


@pytest.mark.parametrize(
    ("name", "dp_id", "mapping"),
    [
        (
            "Frequency",
            "101",
            {
                "3_days": "Every 3 Days",
                "Weekly": "Weekly",
                "Monthly": "Monthly",
                "3_Months": "Every 3 Months",
                "6_Months": "Every 6 Months",
            },
        ),
        ("Duration", "103", {"15": "15 s", "30": "30 s", "45": "45 s", "60": "60 s"}),
    ],
)
@pytest.mark.asyncio
async def test_select_options(mocker, name, dp_id, mapping):
    """Every displayed option reads and writes the corresponding raw enum."""
    config = get_config("the_unclog")
    entity_config = next(e for e in config.all_entities() if e.name == name)
    payload = THE_UNCLOG_PAYLOAD.copy()
    device = mock_device(payload, mocker)
    entity = TuyaLocalSelect(device, entity_config)
    assert entity.options == list(mapping.values())
    for raw, label in mapping.items():
        payload[dp_id] = raw
        assert entity.current_option == label
        async with assert_device_properties_set(device, {dp_id: raw}):
            await entity.async_select_option(label)


@pytest.mark.asyncio
async def test_cleaning_switch_and_status(mocker):
    """DP 1 controls cleaning and follows self-reset; DP 102 reports status."""
    entities = list(get_config("the_unclog").all_entities())
    payload = THE_UNCLOG_PAYLOAD.copy()
    device = mock_device(payload, mocker)
    switch = TuyaLocalSwitch(device, entities[0])
    status = TuyaLocalBinarySensor(device, entities[3])
    async with assert_device_properties_set(device, {"1": True}):
        await switch.async_turn_on()
    payload["1"] = True
    assert switch.is_on is True
    payload["1"] = False
    assert switch.is_on is False
    async with assert_device_properties_set(device, {"1": False}):
        await switch.async_turn_off()
    payload["102"] = False
    assert status.is_on is False
    payload["102"] = True
    assert status.is_on is True
