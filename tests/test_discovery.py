"""Tests for the active Tuya LAN rediscovery sweeper."""

import logging

import pytest
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DATA_DISCOVERY,
    DOMAIN,
)
from custom_components.tuya_local.helpers import discovery
from custom_components.tuya_local.helpers.discovery import (
    TuyaLANRediscovery,
    async_start_discovery,
    async_stop_discovery,
)

TESTKEY = ")<jO<@)'P1|kR$Kd"
DEVID = "bf1234567890abcdef"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def _make_entry(hass, host="192.168.1.10", options=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        minor_version=20,
        title="thermostat",
        data={
            CONF_DEVICE_ID: DEVID,
            CONF_HOST: host,
            CONF_LOCAL_KEY: TESTKEY,
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "polytherm_polyalpha_thermostat",
        },
        options=options or {},
    )
    entry.add_to_hass(hass)
    return entry


def _set_device(hass, returned_state, device_id=DEVID):
    """Register a fake device object in hass.data under the device id."""
    device = type("Dev", (), {"has_returned_state": returned_state})()
    hass.data.setdefault(DOMAIN, {})[device_id] = {"device": device}
    return device


@pytest.mark.asyncio
async def test_sweep_updates_unreachable_changed_host(hass, caplog, mocker):
    """An unreachable device gets relocated, its host updated, and it's logged at WARNING."""
    entry = _make_entry(hass, host="192.168.1.10")
    _set_device(hass, returned_state=False)
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.55", "id": DEVID},
    )

    with caplog.at_level(
        logging.WARNING, logger="custom_components.tuya_local.helpers.discovery"
    ):
        await TuyaLANRediscovery(hass)._async_sweep()
        await hass.async_block_till_done()

    assert entry.data[CONF_HOST] == "192.168.1.55"
    # The IP change must be visible even when the entry runs at WARNING.
    assert "192.168.1.55" in caplog.text
    assert "192.168.1.10" in caplog.text


@pytest.mark.asyncio
async def test_sweep_skips_reachable_device(hass, mocker):
    """A device that is returning state is never scanned."""
    entry = _make_entry(hass, host="192.168.1.10")
    _set_device(hass, returned_state=True)
    find = mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.55"},
    )

    await TuyaLANRediscovery(hass)._async_sweep()
    await hass.async_block_till_done()

    find.assert_not_called()
    assert entry.data[CONF_HOST] == "192.168.1.10"


@pytest.mark.asyncio
async def test_sweep_no_change_when_ip_same(hass, mocker):
    """If the scan returns the current IP, no entry update happens."""
    entry = _make_entry(hass, host="192.168.1.10")
    _set_device(hass, returned_state=False)
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.10"},
    )
    update = mocker.spy(hass.config_entries, "async_update_entry")

    await TuyaLANRediscovery(hass)._async_sweep()
    await hass.async_block_till_done()

    update.assert_not_called()
    assert entry.data[CONF_HOST] == "192.168.1.10"


@pytest.mark.asyncio
async def test_sweep_handles_not_found(hass, mocker):
    """A scan that finds nothing must not raise or change anything."""
    entry = _make_entry(hass, host="192.168.1.10")
    _set_device(hass, returned_state=False)
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": None},
    )
    update = mocker.spy(hass.config_entries, "async_update_entry")

    await TuyaLANRediscovery(hass)._async_sweep()
    await hass.async_block_till_done()

    update.assert_not_called()
    assert entry.data[CONF_HOST] == "192.168.1.10"


@pytest.mark.asyncio
async def test_sweep_updates_host_stored_in_options(hass, mocker):
    """When the effective host lives in options, the update targets options."""
    entry = _make_entry(hass, host="10.0.0.1", options={CONF_HOST: "192.168.1.103"})
    _set_device(hass, returned_state=False)
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.55"},
    )

    await TuyaLANRediscovery(hass)._async_sweep()
    await hass.async_block_till_done()

    assert entry.options[CONF_HOST] == "192.168.1.55"
    assert entry.data[CONF_HOST] == "192.168.1.55"


@pytest.mark.asyncio
async def test_sweep_scans_when_no_device_object(hass, mocker):
    """An entry with no device object yet (failed setup) is still scanned."""
    entry = _make_entry(hass, host="192.168.1.10")
    hass.data.setdefault(DOMAIN, {})  # no device bucket registered
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.77"},
    )

    await TuyaLANRediscovery(hass)._async_sweep()
    await hass.async_block_till_done()

    assert entry.data[CONF_HOST] == "192.168.1.77"


@pytest.mark.asyncio
async def test_start_is_idempotent_and_stop_cancels(hass, mocker):
    """async_start_discovery schedules one interval; stop cancels it."""
    unsub = mocker.MagicMock()
    track = mocker.patch(
        "custom_components.tuya_local.helpers.discovery.async_track_time_interval",
        return_value=unsub,
    )

    await async_start_discovery(hass)
    rediscovery = hass.data[DOMAIN][DATA_DISCOVERY]
    assert isinstance(rediscovery, TuyaLANRediscovery)
    assert track.call_count == 1

    # Second call must not schedule another interval (singleton).
    await async_start_discovery(hass)
    assert track.call_count == 1

    async_stop_discovery(hass)
    unsub.assert_called_once()
    assert DATA_DISCOVERY not in hass.data[DOMAIN]


def test_module_exposes_expected_interval():
    """Guard the sweep cadence against accidental change."""
    assert discovery.SWEEP_INTERVAL.total_seconds() == 60
