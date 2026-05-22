"""Tests for the sensor entity."""

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
from custom_components.tuya_local.sensor import (
    TuyaLocalIPSensor,
    TuyaLocalSensor,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "goldair_dehumidifier",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {"device": m_device},
    }

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["sensor_temperature"]) is TuyaLocalSensor
    # Called twice: once for IP diagnostic sensor, once for DPS-based sensors
    assert m_add_entities.call_count == 2


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_sensor(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "mirabella_genio_usb",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {"device": m_device},
    }
    # No longer raises - IP sensor is still added even without DPS sensors
    await async_setup_entry(hass, entry, m_add_entities)
    # Only the IP diagnostic sensor should be added
    m_add_entities.assert_called_once()
    args = m_add_entities.call_args[0][0]
    assert len(args) == 1
    assert type(args[0]) is TuyaLocalIPSensor


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
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {"device": m_device},
    }
    # No longer raises - IP sensor is still added even without valid config
    await async_setup_entry(hass, entry, m_add_entities)
    # Only the IP diagnostic sensor should be added
    m_add_entities.assert_called_once()
    args = m_add_entities.call_args[0][0]
    assert len(args) == 1
    assert type(args[0]) is TuyaLocalIPSensor


def test_sensor_suggested_display_precision():
    mock_device = Mock()
    config = TuyaEntityConfig(
        mock_device,
        {
            "entity": "sensor",
            "dps": [
                {
                    "id": 1,
                    "name": "sensor",
                    "type": "integer",
                    "precision": 1,
                }
            ],
        },
    )
    sensor = TuyaLocalSensor(mock_device, config)
    assert sensor.suggested_display_precision == 1
    config = TuyaEntityConfig(
        mock_device,
        {
            "entity": "sensor",
            "dps": [{"id": 1, "name": "sensor", "type": "integer"}],
        },
    )
    sensor = TuyaLocalSensor(mock_device, config)
    assert sensor.suggested_display_precision == 0
    config = TuyaEntityConfig(
        mock_device,
        {
            "entity": "sensor",
            "dps": [
                {
                    "id": 1,
                    "name": "sensor",
                    "type": "integer",
                    "mapping": [{"scale": 10}],
                },
            ],
        },
    )
    sensor = TuyaLocalSensor(mock_device, config)
    assert sensor.suggested_display_precision == 1
