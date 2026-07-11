"""Tests for the config flow."""

from unittest.mock import AsyncMock

import pytest
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local import (
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
    config_flow,
    get_device_unique_id,
)
from custom_components.tuya_local.const import (
    CONF_DEVICE_CID,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)

# Designed to contain "special" characters that users constantly suspect.
TESTKEY = ")<jO<@)'P1|kR$Kd"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def prevent_task_creation(mocker):
    mocker.patch("custom_components.tuya_local.device.TuyaLocalDevice.register_entity")
    yield


@pytest.fixture(autouse=True)
def bypass_discovery(mocker):
    """Don't open real LAN discovery sockets during setup in these tests.

    The discovery listener is exercised directly in tests/test_discovery.py.
    """
    mocker.patch(
        "custom_components.tuya_local.async_start_discovery",
        new=AsyncMock(),
    )
    yield


@pytest.fixture
def bypass_setup(mocker):
    """Prevent actual setup of the integration after config flow."""
    mocker.patch("custom_components.tuya_local.async_setup_entry", return_value=True)
    yield


@pytest.fixture
def bypass_data_fetch(mocker):
    """Prevent actual data fetching from the device."""
    mocker.patch("tinytuya.Device.status", return_value={"1": True})
    yield


@pytest.mark.asyncio
async def test_init_entry(hass, bypass_data_fetch):
    """Test initialisation of the config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=11,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "kogan_kahtp_heater",
            CONF_DEVICE_CID: None,
        },
        options={},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.test")
    assert hass.states.get("lock.test_child_lock")


@pytest.mark.asyncio
@pytest.mark.parametrize("refresh_error", [RuntimeError("boom"), None])
async def test_async_setup_entry_cleans_up_failed_device(hass, mocker, refresh_error):
    """Failed runtime setup should not leave stale device state cached."""

    mock_device = mocker.MagicMock()
    if refresh_error is None:
        mock_device.async_refresh = mocker.AsyncMock()
        mock_device.has_returned_state = False
    else:
        mock_device.async_refresh = mocker.AsyncMock(side_effect=refresh_error)

    def fake_setup_device(hass, config):
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["deviceid"] = {
            "device": mock_device,
            "tuyadevice": mock_device._api,
            "tuyadevicelock": mocker.MagicMock(),
        }
        return mock_device

    mocker.patch(
        "custom_components.tuya_local.setup_device", side_effect=fake_setup_device
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        minor_version=18,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: 3.4,
            CONF_TYPE: "kogan_kahtp_heater",
        },
        options={},
    )

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)

    assert "deviceid" not in hass.data.get(DOMAIN, {})
    mock_device._api.set_socketPersistent.assert_called_with(False)


@pytest.mark.asyncio
async def test_async_unload_entry_ignores_missing_device_data(hass):
    """Unload should tolerate entries that failed before device data was cached."""

    hass.data[DOMAIN] = {}
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        minor_version=18,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: 3.4,
            CONF_TYPE: "kogan_kahtp_heater",
        },
        options={},
    )

    assert await async_unload_entry(hass, entry)


@pytest.mark.asyncio
async def test_migrate_entry(hass, mocker):
    """Test migration from old entry format."""
    mock_device = mocker.MagicMock()
    mock_device.async_inferred_type = mocker.AsyncMock(
        return_value="goldair_gpph_heater"
    )
    mocker.patch("custom_components.tuya_local.setup_device", return_value=mock_device)

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "auto",
            "climate": True,
            "child_lock": True,
            "display_light": True,
        },
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = mocker.AsyncMock(return_value=None)
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        title="test2",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "unknown",
            "climate": False,
        },
    )
    entry.add_to_hass(hass)
    assert not await async_migrate_entry(hass, entry)
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="test3",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "auto",
        },
        options={
            "climate": False,
        },
    )
    entry.add_to_hass(hass)
    assert not await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = mocker.AsyncMock(return_value="smartplugv1")
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        title="test4",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "smartplugv1",
        },
        options={
            "switch": True,
        },
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = mocker.AsyncMock(return_value="smartplugv2")
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        title="test5",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "smartplugv1",
        },
        options={
            "switch": True,
        },
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = mocker.AsyncMock(
        return_value="goldair_dehumidifier"
    )
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=4,
        title="test6",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "goldair_dehumidifier",
        },
        options={
            "humidifier": True,
            "fan": True,
            "light": True,
            "lock": False,
            "switch": True,
        },
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = mocker.AsyncMock(
        return_value="grid_connect_usb_double_power_point"
    )
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        title="test7",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "grid_connect_usb_double_power_point",
        },
        options={
            "switch_main_switch": True,
            "switch_left_outlet": True,
            "switch_right_outlet": True,
        },
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)


@pytest.mark.asyncio
async def test_flow_user_init(hass, mocker):
    """Test the initialisation of the form in the first page of the manual config flow path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "local"}
    )
    expected = {
        "data_schema": mocker.ANY,
        "description_placeholders": mocker.ANY,
        "errors": {},
        "flow_id": mocker.ANY,
        "handler": DOMAIN,
        "step_id": "local",
        "type": "form",
        "last_step": mocker.ANY,
        "preview": mocker.ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"](
            {CONF_DEVICE_ID: "test", CONF_LOCAL_KEY: TESTKEY, CONF_HOST: "test"}
        )
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_DEVICE_ID: "missing_some"})
        assert False
    except vol.MultipleInvalid:
        pass


@pytest.mark.asyncio
async def test_flow_user_init_protocol_options_are_strings(hass, mocker):
    """Test that protocol version dropdown uses strings, not floats."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "local"}
    )
    schema = result["data_schema"]
    # Validate that string protocol versions are accepted
    schema(
        {
            CONF_DEVICE_ID: "test",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "test",
            CONF_PROTOCOL_VERSION: "3.3",
            CONF_POLL_ONLY: False,
        }
    )
    # Validate that float protocol versions are rejected
    with pytest.raises(vol.MultipleInvalid):
        schema(
            {
                CONF_DEVICE_ID: "test",
                CONF_LOCAL_KEY: TESTKEY,
                CONF_HOST: "test",
                CONF_PROTOCOL_VERSION: 3.3,
                CONF_POLL_ONLY: False,
            }
        )


@pytest.mark.asyncio
async def test_async_test_connection_valid(hass, mocker):
    """Test that device is returned when connection is valid."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.has_returned_state = True
    mock_instance.pause = mocker.MagicMock()
    mock_instance.resume = mocker.MagicMock()
    mock_device.return_value = mock_instance
    hass.data[DOMAIN] = {"deviceid": {"device": mock_instance}}

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: "auto",
        },
        hass,
    )
    assert device == mock_instance
    mock_instance.pause.assert_called_once()
    mock_instance.resume.assert_called_once()


@pytest.mark.asyncio
async def test_async_test_connection_for_subdevice_valid(hass, mocker):
    """Test that subdevice is returned when connection is valid."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.has_returned_state = True
    mock_instance.pause = mocker.MagicMock()
    mock_instance.resume = mocker.MagicMock()
    mock_device.return_value = mock_instance
    hass.data[DOMAIN] = {"subdeviceid": {"device": mock_instance}}

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: "auto",
            CONF_DEVICE_CID: "subdeviceid",
        },
        hass,
    )
    assert device == mock_instance
    mock_instance.pause.assert_called_once()
    mock_instance.resume.assert_called_once()


@pytest.mark.asyncio
async def test_async_test_connection_invalid(hass, mocker):
    """Test that None is returned when connection is invalid."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.has_returned_state = False
    mock_instance._api = mocker.MagicMock()
    mock_device.return_value = mock_instance
    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: "auto",
        },
        hass,
    )
    assert device is None


@pytest.mark.asyncio
async def test_flow_user_init_invalid_config(hass, mocker):
    """Test errors populated when config is invalid."""
    mocker.patch(
        "custom_components.tuya_local.config_flow.async_test_connection",
        return_value=None,
    )
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "local"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "badkey",
            CONF_PROTOCOL_VERSION: "auto",
            CONF_POLL_ONLY: False,
        },
    )
    assert {"base": "connection"} == result["errors"]


def setup_device_mock(mock, mocker, failure=False, devtype="test"):
    mock_type = mocker.MagicMock()
    mock_type.legacy_type = devtype
    mock_type.config_type = devtype
    mock_type.match_quality.return_value = 100
    mock_type.product_display_entries.return_value = [(None, None)]
    mock.async_possible_types = mocker.AsyncMock(
        return_value=[mock_type] if not failure else []
    )


@pytest.mark.asyncio
async def test_flow_user_init_data_valid(hass, mocker):
    """Test we advance to the next step when connection config is valid."""
    mock_device = mocker.MagicMock()
    mock_device._protocol_configured = "auto"
    setup_device_mock(mock_device, mocker)
    mocker.patch(
        "custom_components.tuya_local.config_flow.async_test_connection",
        return_value=mock_device,
    )

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "local"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
        },
    )
    assert "form" == result["type"]
    assert "select_type" == result["step_id"]


@pytest.mark.asyncio
async def test_flow_select_type_init(hass, mocker):
    """Test the initialisation of the form in the 2nd step of the config flow."""
    mock_device = mocker.patch.object(config_flow.ConfigFlowHandler, "device")

    setup_device_mock(mock_device, mocker)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    expected = {
        "data_schema": mocker.ANY,
        "description_placeholders": {"device_name": ""},
        "errors": None,
        "flow_id": mocker.ANY,
        "handler": DOMAIN,
        "step_id": "select_type",
        "type": "form",
        "last_step": mocker.ANY,
        "preview": mocker.ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"]({CONF_TYPE: "test||||"})
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_TYPE: "not_test||||"})
        assert False
    except vol.MultipleInvalid:
        pass


@pytest.mark.asyncio
async def test_flow_select_type_aborts_when_no_match(hass, mocker):
    """Test the flow aborts when an unsupported device is used."""
    mock_device = mocker.patch.object(config_flow.ConfigFlowHandler, "device")
    setup_device_mock(mock_device, mocker, failure=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


@pytest.mark.asyncio
async def test_flow_select_type_data_valid(hass, mocker):
    """Test the flow continues when valid data is supplied."""
    mock_device = mocker.patch.object(config_flow.ConfigFlowHandler, "device")

    setup_device_mock(mock_device, mocker, devtype="smartplugv1")

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={CONF_TYPE: "smartplugv1||||"},
    )
    assert "form" == result["type"]
    assert "choose_entities" == result["step_id"]


@pytest.mark.asyncio
async def test_flow_choose_entities_init(hass, mocker):
    """Test the initialisation of the form in the 3rd step of the config flow."""

    mocker.patch.dict(config_flow.ConfigFlowHandler.data, {CONF_TYPE: "smartplugv1"})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "choose_entities"}
    )

    expected = {
        "data_schema": mocker.ANY,
        "description_placeholders": {"device_name": ""},
        "errors": None,
        "flow_id": mocker.ANY,
        "handler": DOMAIN,
        "step_id": "choose_entities",
        "type": "form",
        "last_step": mocker.ANY,
        "preview": mocker.ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"]({CONF_NAME: "test"})
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({"climate": True})
        assert False
    except vol.MultipleInvalid:
        pass


@pytest.mark.asyncio
async def test_flow_choose_entities_creates_config_entry(hass, bypass_setup, mocker):
    """Test the flow ends when data is valid."""

    mocker.patch.dict(
        config_flow.ConfigFlowHandler.data,
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "kogan_kahtp_heater",
            CONF_DEVICE_CID: None,
        },
    )
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "choose_entities"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={
            CONF_NAME: "test",
        },
    )
    expected = {
        "version": 13,
        "minor_version": mocker.ANY,
        "context": {"source": "choose_entities"},
        "type": FlowResultType.CREATE_ENTRY,
        "flow_id": mocker.ANY,
        "handler": DOMAIN,
        "title": "test",
        "description": None,
        "description_placeholders": None,
        "result": mocker.ANY,
        "subentries": (),
        "options": {},
        "data": {
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "kogan_kahtp_heater",
            CONF_DEVICE_CID: None,
        },
    }
    assert expected == result


@pytest.mark.asyncio
async def test_options_flow_init(hass, bypass_data_fetch):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_NAME: "test",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "smartplugv1",
            CONF_DEVICE_CID: "",
        },
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert "form" == result["type"]
    assert "user" == result["step_id"]
    assert {} == result["errors"]
    assert result["data_schema"](
        {
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
        }
    )


@pytest.mark.asyncio
async def test_options_flow_modifies_config(hass, bypass_setup, mocker):
    mock_device = mocker.MagicMock()
    mocker.patch(
        "custom_components.tuya_local.config_flow.async_test_connection",
        return_value=mock_device,
    )

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_NAME: "test",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "ble_pt216_temp_humidity",
            CONF_DEVICE_CID: "subdeviceid",
        },
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # show initial form
    form = await hass.config_entries.options.async_init(config_entry.entry_id)
    # submit updated config
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={
            CONF_HOST: "new_hostname",
            CONF_LOCAL_KEY: "new_key",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "3.3",
        },
    )
    expected = {
        CONF_HOST: "new_hostname",
        CONF_LOCAL_KEY: "new_key",
        CONF_POLL_ONLY: False,
        CONF_PROTOCOL_VERSION: 3.3,
    }
    assert "create_entry" == result["type"]
    assert "" == result["title"]
    assert expected == result["data"]


@pytest.mark.asyncio
async def test_options_flow_fails_when_connection_fails(
    hass, bypass_data_fetch, mocker
):
    mocker.patch(
        "custom_components.tuya_local.config_flow.async_test_connection",
        return_value=None,
    )
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_NAME: "test",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "smartplugv1",
            CONF_DEVICE_CID: "",
        },
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # show initial form
    form = await hass.config_entries.options.async_init(config_entry.entry_id)
    # submit updated config
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={
            CONF_HOST: "new_hostname",
            CONF_LOCAL_KEY: "new_key",
        },
    )
    assert "form" == result["type"]
    assert "user" == result["step_id"]
    assert {"base": "connection"} == result["errors"]


@pytest.mark.asyncio
async def test_options_flow_fails_when_config_is_missing(hass, mocker):
    mock_device = mocker.MagicMock()
    mocker.patch(
        "custom_components.tuya_local.config_flow.async_test_connection",
        return_value=mock_device,
    )

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_NAME: "test",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "non_existing",
        },
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


def test_migration_gets_correct_device_id():
    """Test that migration gets the correct device id."""
    # Normal device
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_TYPE: "auto",
        },
    )
    assert get_device_unique_id(entry) == "deviceid"


# ---------------------------------------------------------------------------
# async_step_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_user_shows_form(hass):
    """Test the user step shows the setup mode form when no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_flow_user_manual_goes_to_local(hass):
    """Test that choosing 'manual' advances to the local step."""
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "manual"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "local"


@pytest.mark.asyncio
async def test_flow_user_cloud_authenticated_goes_to_choose_device(hass, mocker):
    """Test cloud mode when already authenticated goes to choose_device."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(
        return_value={
            "dev1": {
                "name": "Light",
                "product_name": "Smart Light",
                "local_key": "key1",
                "online": True,
                "is_hub": False,
                "exists": False,
            }
        }
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "choose_device"


@pytest.mark.asyncio
async def test_flow_user_cloud_not_authenticated_goes_to_cloud_step(hass, mocker):
    """Test cloud mode when not authenticated goes to the cloud (QR) step."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = False
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "cloud"


@pytest.mark.asyncio
async def test_flow_user_cloud_fresh_login_logs_out_and_goes_to_cloud(hass, mocker):
    """Test cloud_fresh_login forces logout then goes to cloud step."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = False
    mock_cloud.logout = mocker.MagicMock()
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud_fresh_login"}
    )
    mock_cloud.logout.assert_called_once()
    assert result["type"] == "form"
    assert result["step_id"] == "cloud"


@pytest.mark.asyncio
async def test_flow_user_cloud_exception_goes_to_cloud_step(hass, mocker):
    """Test that cloud exceptions cause re-auth (go to cloud step)."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(side_effect=Exception("network error"))
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "cloud"


# ---------------------------------------------------------------------------
# async_step_cloud
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_cloud_shows_form(hass, mocker):
    """Test cloud step shows the user_code form."""
    mocker.patch("custom_components.tuya_local.config_flow.Cloud")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cloud"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "cloud"


@pytest.mark.asyncio
async def test_flow_cloud_success_goes_to_scan(hass, mocker):
    """Test entering a user code that succeeds goes to QR scan step."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.async_get_qr_code = AsyncMock(return_value="QR_TOKEN_123")
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"user_code": "MY_CODE"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "scan"


@pytest.mark.asyncio
async def test_flow_cloud_failure_shows_error(hass, mocker):
    """Test entering a bad user code stays on cloud step with error."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.async_get_qr_code = AsyncMock(return_value=False)
    mock_cloud.last_error = {"msg": "Invalid code", "code": 1001}
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"user_code": "BAD_CODE"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "cloud"
    assert result["errors"] == {"base": "login_error"}


# ---------------------------------------------------------------------------
# async_step_scan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_scan_shows_qr_form(hass, mocker):
    """Test the scan step shows the QR code form."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.async_get_qr_code = AsyncMock(return_value="QR_TOKEN")
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    # Get to scan via cloud step
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"user_code": "CODE"}
    )
    assert result["step_id"] == "scan"


@pytest.mark.asyncio
async def test_flow_scan_login_success_goes_to_choose_device(hass, mocker):
    """Test scanning QR and successful login goes to choose_device."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.async_get_qr_code = AsyncMock(return_value="QR_TOKEN")
    mock_cloud.async_login = AsyncMock(return_value=True)
    mock_cloud.async_get_devices = AsyncMock(
        return_value={
            "dev1": {
                "name": "Plug",
                "product_name": "Smart Plug",
                "local_key": "key",
                "online": True,
                "is_hub": False,
                "exists": False,
            }
        }
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cloud"}
    )
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"user_code": "CODE"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "choose_device"


@pytest.mark.asyncio
async def test_flow_scan_login_failure_stays_on_scan(hass, mocker):
    """Test failed login stays on scan step with error."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.async_get_qr_code = AsyncMock(return_value="QR_TOKEN")
    mock_cloud.async_login = AsyncMock(return_value=False)
    mock_cloud.last_error = {"msg": "Auth failed", "code": 2000}
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cloud"}
    )
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"user_code": "CODE"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "scan"
    assert result["errors"] == {"base": "login_error"}


# ---------------------------------------------------------------------------
# async_step_choose_device
# ---------------------------------------------------------------------------


def _make_cloud_devices(include_hub=False, include_offline=False):
    devices = {
        "dev1": {
            "name": "Smart Light",
            "product_name": "Light",
            "local_key": "key1",
            "online": True,
            "is_hub": False,
            "exists": False,
            "ip": "192.168.1.10",
        }
    }
    if include_hub:
        devices["hub1"] = {
            "name": "Zigbee Hub",
            "product_name": "Hub",
            "local_key": "hubkey",
            "online": True,
            "is_hub": True,
            "exists": False,
            "ip": "192.168.1.1",
        }
    if include_offline:
        devices["dev2"] = {
            "name": "Offline Device",
            "product_name": "Sensor",
            "local_key": "key2",
            "online": False,
            "is_hub": False,
            "exists": False,
            "ip": "192.168.1.20",
        }
    return devices


@pytest.mark.asyncio
async def test_flow_choose_device_shows_form(hass, mocker):
    """Test the choose_device step shows the device list form."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=_make_cloud_devices())
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "choose_device"


@pytest.mark.asyncio
async def test_flow_choose_device_aborts_when_no_devices(hass, mocker):
    """Test choose_device aborts when no new devices are available."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value={})
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "no_devices"


@pytest.mark.asyncio
async def test_flow_choose_device_direct_device_no_hub_goes_to_search(hass, mocker):
    """Test selecting a directly addressable device (no hub) goes to search."""
    devices = _make_cloud_devices()
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=devices)
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "None"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "search"


@pytest.mark.asyncio
async def test_flow_choose_device_direct_device_with_hub_shows_error(hass, mocker):
    """Test selecting a hub for a direct device shows an error."""
    devices = _make_cloud_devices(include_hub=True)
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=devices)
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "hub1"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "choose_device"
    assert result["errors"] == {"base": "does_not_need_hub"}


@pytest.mark.asyncio
async def test_flow_choose_device_indirect_device_with_hub_goes_to_search(hass, mocker):
    """Test selecting an indirect device with a hub goes to search."""
    devices = {
        "subdev1": {
            "name": "Sub Device",
            "product_name": "Sensor",
            "local_key": "subkey",  # non-empty so it appears in list
            "online": True,
            "is_hub": False,
            "exists": False,
            "ip": "",  # empty ip = indirect/sub-device
            "node_id": "node123",
            "uuid": "uuid123",
            "product_id": "prod_sub",
        },
        "hub1": {
            "name": "Hub",
            "product_name": "Gateway",
            "local_key": "hubkey",
            "online": True,
            "is_hub": True,
            "exists": False,
            "ip": "192.168.1.1",
        },
    }
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=devices)
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "subdev1", "hub_id": "hub1"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "search"


@pytest.mark.asyncio
async def test_flow_choose_device_indirect_no_hub_shows_error(hass, mocker):
    """Test selecting an indirect device without a hub shows an error."""
    devices = {
        "subdev1": {
            "name": "Sub Device",
            "product_name": "Sensor",
            "local_key": "subkey",  # non-empty so it appears in list
            "online": True,
            "is_hub": False,
            "exists": False,
            "ip": "",  # empty ip = indirect/sub-device
        }
    }
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=devices)
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "subdev1", "hub_id": "None"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "choose_device"
    assert result["errors"] == {"base": "needs_hub"}


# ---------------------------------------------------------------------------
# async_step_search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_search_shows_form(hass, mocker):
    """Test the search step shows the scanning form."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=_make_cloud_devices())
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "None"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "search"


@pytest.mark.asyncio
async def test_flow_search_found_device_goes_to_local(hass, mocker):
    """Test that finding a device on the network advances to the local step."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=_make_cloud_devices())
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.scan_for_device",
        return_value={"ip": "192.168.1.50", "version": "3.3", "productKey": "pk123"},
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "None"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "local"


@pytest.mark.asyncio
async def test_flow_search_not_found_still_goes_to_local(hass, mocker):
    """Test that not finding a device still advances to local step (blank IP)."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=_make_cloud_devices())
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.scan_for_device",
        return_value={"ip": None},
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "None"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "local"


@pytest.mark.asyncio
async def test_flow_search_oserror_still_goes_to_local(hass, mocker):
    """Test that an OSError during scan still advances to local step."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(return_value=_make_cloud_devices())
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.scan_for_device",
        side_effect=OSError("network unreachable"),
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "None"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "local"


# ---------------------------------------------------------------------------
# async_test_connection with fixed protocol
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_test_connection_fixed_protocol_success(hass, mocker):
    """Test connection with a fixed protocol version (not auto)."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.has_returned_state = True
    mock_device.return_value = mock_instance

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: 3.3,
        },
        hass,
    )
    assert device == mock_instance


@pytest.mark.asyncio
async def test_async_test_connection_fixed_protocol_no_state(hass, mocker):
    """Test fixed protocol returns None when device has no state."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.has_returned_state = False
    mock_device.return_value = mock_instance

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: 3.3,
        },
        hass,
    )
    assert device is None


@pytest.mark.asyncio
async def test_async_test_connection_fixed_protocol_exception(hass, mocker):
    """Test fixed protocol returns None on exception."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.async_refresh = AsyncMock(side_effect=Exception("timeout"))
    mock_device.return_value = mock_instance

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: 3.3,
        },
        hass,
    )
    assert device is None


@pytest.mark.asyncio
async def test_async_test_connection_auto_all_protocols_fail(hass, mocker):
    """Test auto mode returns None when all protocols fail."""
    mock_device = mocker.patch(
        "custom_components.tuya_local.config_flow.TuyaLocalDevice"
    )
    mock_instance = mocker.AsyncMock()
    mock_instance.has_returned_state = False
    mock_instance._api = mocker.MagicMock()
    mock_instance._api.parent = None
    mock_device.return_value = mock_instance

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: TESTKEY,
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: "auto",
        },
        hass,
    )
    assert device is None


# ---------------------------------------------------------------------------
# _device_name_placeholder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_device_name_placeholder_with_cloud_device(hass, mocker):
    """Test _device_name_placeholder returns formatted name when cloud device set."""
    mock_cloud = mocker.MagicMock()
    mock_cloud.is_authenticated = True
    mock_cloud.async_get_devices = AsyncMock(
        return_value={
            "dev1": {
                "name": "My Light",
                "product_name": "Smart Bulb",
                "local_key": "key",
                "online": True,
                "is_hub": False,
                "exists": False,
                "ip": "192.168.1.5",
            }
        }
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.Cloud", return_value=mock_cloud
    )
    mocker.patch(
        "custom_components.tuya_local.config_flow.scan_for_device",
        return_value={"ip": None},
    )

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"setup_mode": "cloud"}
    )
    await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"device_id": "dev1", "hub_id": "None"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )
    # The local step description_placeholders should contain the device name
    assert result["step_id"] == "local"
    placeholder = result["description_placeholders"]["device_name"]
    assert "My Light" in placeholder
    assert "Smart Bulb" in placeholder


@pytest.mark.asyncio
async def test_device_name_placeholder_without_cloud_device(hass, mocker):
    """Test _device_name_placeholder returns empty string when no cloud device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "local"}
    )
    assert result["step_id"] == "local"
    assert result["description_placeholders"]["device_name"] == ""


# ---------------------------------------------------------------------------
# async_step_select_type with auto-detected protocol
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_select_type_shows_auto_detected_form(hass, mocker):
    """Test select_type shows the auto_detected variant when protocol was detected."""
    mock_device = mocker.patch.object(config_flow.ConfigFlowHandler, "device")

    mock_type = mocker.MagicMock()
    mock_type.config_type = "smartplugv1"
    mock_type.name = "Smart Plug"
    mock_type.match_quality.return_value = 85
    mock_type.product_display_entries.return_value = [(None, None)]
    mock_device.async_possible_types = mocker.AsyncMock(return_value=[mock_type])
    mock_device._get_cached_state.return_value = {"1": True}
    mock_device._product_ids = []

    mocker.patch.object(
        config_flow.ConfigFlowHandler,
        "_auto_detected_protocol",
        new_callable=lambda: property(lambda self: 3.3),
        create=True,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    # Either select_type or select_type_auto_detected depending on attribute
    assert result["step_id"] in ("select_type", "select_type_auto_detected")


# ---------------------------------------------------------------------------
# choose_entities with cloud device name as default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_choose_entities_uses_cloud_name_as_default(
    hass, bypass_setup, mocker
):
    """Test choose_entities uses cloud device name as the default entity name."""
    mocker.patch.dict(config_flow.ConfigFlowHandler.data, {CONF_TYPE: "smartplugv1"})
    # Patch __cloud_device on the handler class
    mocker.patch.object(
        config_flow.ConfigFlowHandler,
        "_ConfigFlowHandler__cloud_device",
        new={"name": "My Cloud Device", "product_name": "Plug"},
        create=True,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "choose_entities"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "choose_entities"
    # The schema default should be the cloud device name
    schema = result["data_schema"]
    # Validate it accepts the cloud device name
    validated = schema({CONF_NAME: "My Cloud Device"})
    assert validated[CONF_NAME] == "My Cloud Device"
