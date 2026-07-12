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
    """async_start_discovery schedules the sweep + scan intervals; stop cancels both."""
    unsub_sweep = mocker.MagicMock()
    unsub_scan = mocker.MagicMock()
    track = mocker.patch(
        "custom_components.tuya_local.helpers.discovery.async_track_time_interval",
        side_effect=[unsub_sweep, unsub_scan],
    )

    await async_start_discovery(hass)
    rediscovery = hass.data[DOMAIN][DATA_DISCOVERY]
    assert isinstance(rediscovery, TuyaLANRediscovery)
    assert track.call_count == 2

    # Second call must not schedule more intervals (singleton).
    await async_start_discovery(hass)
    assert track.call_count == 2

    async_stop_discovery(hass)
    unsub_sweep.assert_called_once()
    unsub_scan.assert_called_once()
    assert DATA_DISCOVERY not in hass.data[DOMAIN]


def _fake_config(matches):
    """Minimal stand-in for a device config with a matches_product() method."""
    return type("Cfg", (), {"matches_product": lambda self, pid: matches})()


@pytest.mark.asyncio
async def test_product_scan_warns_once_on_unmatched_product(hass, caplog, mocker):
    """An unmatched product id is logged at WARNING, once per device per run."""
    _make_entry(hass, host="192.168.1.10")
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.10", "product_id": "keyabc123"},
    )
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery.get_config",
        return_value=_fake_config(False),
    )
    disc = TuyaLANRediscovery(hass)

    with caplog.at_level(
        logging.WARNING, logger="custom_components.tuya_local.helpers.discovery"
    ):
        await disc._async_product_scan()
        await hass.async_block_till_done()
        assert caplog.text.count("keyabc123") == 1
        # A second scan must not warn again for the same device.
        caplog.clear()
        await disc._async_product_scan()
        await hass.async_block_till_done()
        assert "keyabc123" not in caplog.text


@pytest.mark.asyncio
async def test_product_scan_silent_when_product_matches(hass, caplog, mocker):
    """No warning when the product id is listed in the config."""
    _make_entry(hass, host="192.168.1.10")
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.10", "product_id": "keyabc123"},
    )
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery.get_config",
        return_value=_fake_config(True),
    )
    with caplog.at_level(
        logging.WARNING, logger="custom_components.tuya_local.helpers.discovery"
    ):
        await TuyaLANRediscovery(hass)._async_product_scan()
        await hass.async_block_till_done()
    assert "is not listed" not in caplog.text


@pytest.mark.asyncio
async def test_product_scan_skips_when_no_product_id(hass, mocker):
    """If the scan returns no product id, the config is not even looked up."""
    _make_entry(hass, host="192.168.1.10")
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.10"},
    )
    get_config = mocker.patch(
        "custom_components.tuya_local.helpers.discovery.get_config",
    )
    await TuyaLANRediscovery(hass)._async_product_scan()
    await hass.async_block_till_done()
    get_config.assert_not_called()


@pytest.mark.asyncio
async def test_product_scan_handles_missing_config(hass, caplog, mocker):
    """A missing config file must not warn or raise."""
    _make_entry(hass, host="192.168.1.10")
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery._find_device",
        return_value={"ip": "192.168.1.10", "product_id": "keyabc123"},
    )
    mocker.patch(
        "custom_components.tuya_local.helpers.discovery.get_config",
        return_value=None,
    )
    with caplog.at_level(
        logging.WARNING, logger="custom_components.tuya_local.helpers.discovery"
    ):
        await TuyaLANRediscovery(hass)._async_product_scan()
        await hass.async_block_till_done()
    assert "keyabc123" not in caplog.text


def test_module_exposes_expected_intervals():
    """Guard the cadences against accidental change."""
    assert discovery.SWEEP_INTERVAL.total_seconds() == 60
    assert discovery.SCAN_INTERVAL.total_seconds() == 600
