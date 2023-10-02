"""Tests for the config flow."""
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local import (
    async_migrate_entry,
    async_setup_entry,
    config_flow,
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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def prevent_task_creation():
    with patch(
        "custom_components.tuya_local.device.TuyaLocalDevice.register_entity",
    ):
        yield


@pytest.fixture
def bypass_setup():
    """Prevent actual setup of the integration after config flow."""
    with patch(
        "custom_components.tuya_local.async_setup_entry",
        return_value=True,
    ):
        yield


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test initialisation of the config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=11,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
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
@patch("custom_components.tuya_local.setup_device")
async def test_migrate_entry(mock_setup, hass):
    """Test migration from old entry format."""
    mock_device = MagicMock()
    mock_device.async_inferred_type = AsyncMock(return_value="goldair_gpph_heater")
    mock_setup.return_value = mock_device

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "auto",
            "climate": True,
            "child_lock": True,
            "display_light": True,
        },
    )
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = AsyncMock(return_value=None)
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        title="test2",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "unknown",
            "climate": False,
        },
    )
    assert not await async_migrate_entry(hass, entry)
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="test3",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "auto",
        },
        options={
            "climate": False,
        },
    )
    assert not await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = AsyncMock(return_value="smartplugv1")
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        title="test4",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "smartplugv1",
        },
        options={
            "switch": True,
        },
    )
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = AsyncMock(return_value="smartplugv2")
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        title="test5",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "smartplugv1",
        },
        options={
            "switch": True,
        },
    )
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = AsyncMock(return_value="goldair_dehumidifier")
    mock_device.reset_mock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=4,
        title="test6",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
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
    assert await async_migrate_entry(hass, entry)

    mock_device.async_inferred_type = AsyncMock(
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
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "grid_connect_usb_double_power_point",
        },
        options={
            "switch_main_switch": True,
            "switch_left_outlet": True,
            "switch_right_outlet": True,
        },
    )
    assert await async_migrate_entry(hass, entry)


@pytest.mark.asyncio
async def test_flow_user_init(hass):
    """Test the initialisation of the form in the first step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    expected = {
        "data_schema": ANY,
        "description_placeholders": None,
        "errors": {},
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "user",
        "type": "form",
        "last_step": ANY,
        "preview": ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"](
            {CONF_DEVICE_ID: "test", CONF_LOCAL_KEY: "test", CONF_HOST: "test"}
        )
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_DEVICE_ID: "missing_some"})
        assert False
    except vol.MultipleInvalid:
        pass


@pytest.mark.asyncio
@patch("custom_components.tuya_local.config_flow.TuyaLocalDevice")
async def test_async_test_connection_valid(mock_device, hass):
    """Test that device is returned when connection is valid."""
    mock_instance = AsyncMock()
    mock_instance.has_returned_state = True
    mock_device.return_value = mock_instance
    hass.data[DOMAIN] = {"deviceid": {"device": mock_instance}}

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: "auto",
        },
        hass,
    )
    assert device == mock_instance
    mock_instance.pause.assert_called_once()
    mock_instance.resume.assert_called_once()


@pytest.mark.asyncio
@patch("custom_components.tuya_local.config_flow.TuyaLocalDevice")
async def test_async_test_connection_for_subdevice_valid(mock_device, hass):
    """Test that subdevice is returned when connection is valid."""
    mock_instance = AsyncMock()
    mock_instance.has_returned_state = True
    mock_device.return_value = mock_instance
    hass.data[DOMAIN] = {"subdeviceid": {"device": mock_instance}}

    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
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
@patch("custom_components.tuya_local.config_flow.TuyaLocalDevice")
async def test_async_test_connection_invalid(mock_device, hass):
    """Test that None is returned when connection is invalid."""
    mock_instance = AsyncMock()
    mock_instance.has_returned_state = False
    mock_device.return_value = mock_instance
    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
            CONF_PROTOCOL_VERSION: "auto",
        },
        hass,
    )
    assert device is None


@pytest.mark.asyncio
@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_flow_user_init_invalid_config(mock_test, hass):
    """Test errors populated when config is invalid."""
    mock_test.return_value = None
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
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


def setup_device_mock(mock, failure=False, type="test"):
    mock_type = MagicMock()
    mock_type.legacy_type = type
    mock_type.config_type = type
    mock_type.match_quality.return_value = 100
    mock_iter = MagicMock()
    mock_iter.__aiter__.return_value = [mock_type] if not failure else []
    mock.async_possible_types = MagicMock(return_value=mock_iter)


@pytest.mark.asyncio
@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_flow_user_init_data_valid(mock_test, hass):
    """Test we advance to the next step when connection config is valid."""
    mock_device = MagicMock()
    setup_device_mock(mock_device)
    mock_test.return_value = mock_device

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
        },
    )
    assert "form" == result["type"]
    assert "select_type" == result["step_id"]


@pytest.mark.asyncio
@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_init(mock_device, hass):
    """Test the initialisation of the form in the 2nd step of the config flow."""
    setup_device_mock(mock_device)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    expected = {
        "data_schema": ANY,
        "description_placeholders": None,
        "errors": None,
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "select_type",
        "type": "form",
        "last_step": ANY,
        "preview": ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"]({CONF_TYPE: "test"})
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_TYPE: "not_test"})
        assert False
    except vol.MultipleInvalid:
        pass


@pytest.mark.asyncio
@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_aborts_when_no_match(mock_device, hass):
    """Test the flow aborts when an unsupported device is used."""
    setup_device_mock(mock_device, failure=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


@pytest.mark.asyncio
@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_data_valid(mock_device, hass):
    """Test the flow continues when valid data is supplied."""
    setup_device_mock(mock_device, type="smartplugv1")

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={CONF_TYPE: "smartplugv1"},
    )
    assert "form" == result["type"]
    assert "choose_entities" == result["step_id"]


@pytest.mark.asyncio
async def test_flow_choose_entities_init(hass):
    """Test the initialisation of the form in the 3rd step of the config flow."""

    with patch.dict(config_flow.ConfigFlowHandler.data, {CONF_TYPE: "smartplugv1"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "choose_entities"}
        )

    expected = {
        "data_schema": ANY,
        "description_placeholders": None,
        "errors": None,
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "choose_entities",
        "type": "form",
        "last_step": ANY,
        "preview": ANY,
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
async def test_flow_choose_entities_creates_config_entry(hass, bypass_setup):
    """Test the flow ends when data is valid."""

    with patch.dict(
        config_flow.ConfigFlowHandler.data,
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: "auto",
            CONF_TYPE: "kogan_kahtp_heater",
            CONF_DEVICE_CID: None,
        },
    ):
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
            "context": {"source": "choose_entities"},
            "type": "create_entry",
            "flow_id": ANY,
            "handler": DOMAIN,
            "title": "test",
            "description": None,
            "description_placeholders": None,
            "result": ANY,
            "options": {},
            "data": {
                CONF_DEVICE_ID: "deviceid",
                CONF_HOST: "hostname",
                CONF_LOCAL_KEY: "localkey",
                CONF_POLL_ONLY: False,
                CONF_PROTOCOL_VERSION: "auto",
                CONF_TYPE: "kogan_kahtp_heater",
                CONF_DEVICE_CID: None,
            },
        }
        assert expected == result


@pytest.mark.asyncio
async def test_options_flow_init(hass):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
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
            CONF_LOCAL_KEY: "localkey",
        }
    )


@pytest.mark.asyncio
@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_modifies_config(mock_test, hass):
    mock_device = MagicMock()
    mock_test.return_value = mock_device

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
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
            CONF_PROTOCOL_VERSION: 3.3,
            CONF_DEVICE_CID: "subdeviceid",
        },
    )
    expected = {
        CONF_HOST: "new_hostname",
        CONF_LOCAL_KEY: "new_key",
        CONF_POLL_ONLY: False,
        CONF_PROTOCOL_VERSION: 3.3,
        CONF_DEVICE_CID: "subdeviceid",
    }
    assert "create_entry" == result["type"]
    assert "" == result["title"]
    assert result["result"] is True
    assert expected == result["data"]


@pytest.mark.asyncio
@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_fails_when_connection_fails(mock_test, hass):
    mock_test.return_value = None

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
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
@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_fails_when_config_is_missing(mock_test, hass):
    mock_device = MagicMock()
    mock_test.return_value = mock_device

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
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


@pytest.mark.asyncio
@patch("custom_components.tuya_local.setup_device")
async def test_async_setup_entry_for_switch(mock_device, hass):
    """Test setting up based on a config entry.  Repeats test_init_entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=13,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_POLL_ONLY: False,
            CONF_PROTOCOL_VERSION: 3.3,
            CONF_TYPE: "smartplugv2",
        },
    )
    assert await async_setup_entry(hass, config_entry)
