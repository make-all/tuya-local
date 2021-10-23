"""Tests for the config flow."""
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_NAME
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

import voluptuous as vol

from custom_components.tuya_local import (
    config_flow,
    async_migrate_entry,
    async_setup_entry,
)
from custom_components.tuya_local.const import (
    CONF_CLIMATE,
    CONF_DEVICE_ID,
    CONF_FAN,
    CONF_HUMIDIFIER,
    CONF_LIGHT,
    CONF_LOCAL_KEY,
    CONF_LOCK,
    CONF_SWITCH,
    CONF_TYPE,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def bypass_setup():
    """Prevent actual setup of the integration after config flow."""
    with patch(
        "custom_components.tuya_local.async_setup_entry",
        return_value=True,
    ):
        yield


async def test_init_entry(hass):
    """Test initialisation of the config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "kogan_kahtp_heater",
            CONF_CLIMATE: True,
            "lock_child_lock": True,
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.test")
    assert hass.states.get("lock.test_child_lock")


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
            CONF_CLIMATE: True,
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
            CONF_CLIMATE: False,
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
            CONF_CLIMATE: False,
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
            CONF_SWITCH: True,
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
            CONF_SWITCH: True,
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
            CONF_HUMIDIFIER: True,
            CONF_FAN: True,
            CONF_LIGHT: True,
            CONF_LOCK: False,
            CONF_SWITCH: True,
        },
    )
    assert await async_migrate_entry(hass, entry)


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


@patch("custom_components.tuya_local.config_flow.TuyaLocalDevice")
async def test_async_test_connection_valid(mock_device, hass):
    """Test that device is returned when connection is valid."""
    mock_instance = AsyncMock()
    mock_instance.has_returned_state = True
    mock_device.return_value = mock_instance
    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
        },
        hass,
    )
    assert device == mock_instance


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
        },
        hass,
    )
    assert device is None


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


@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_aborts_when_no_match(mock_device, hass):
    """Test the flow aborts when an unsupported device is used."""
    setup_device_mock(mock_device, failure=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_data_valid(mock_device, hass):
    """Test the flow continues when valid data is supplied."""
    setup_device_mock(mock_device, type="kogan_switch")

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={CONF_TYPE: "kogan_switch"},
    )
    assert "form" == result["type"]
    assert "choose_entities" == result["step_id"]


async def test_flow_choose_entities_init(hass):
    """Test the initialisation of the form in the 3rd step of the config flow."""

    with patch.dict(config_flow.ConfigFlowHandler.data, {CONF_TYPE: "kogan_switch"}):
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
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"]({CONF_NAME: "test", CONF_SWITCH: True})
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_CLIMATE: True})
        assert False
    except vol.MultipleInvalid:
        pass


async def test_flow_choose_entities_creates_config_entry(hass, bypass_setup):
    """Test the flow ends when data is valid."""

    with patch.dict(
        config_flow.ConfigFlowHandler.data,
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
            CONF_TYPE: "kogan_kahtp_heater",
        },
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "choose_entities"}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={
                CONF_NAME: "test",
                CONF_CLIMATE: True,
                "lock_child_lock": False,
            },
        )
        expected = {
            "version": 6,
            "type": "create_entry",
            "flow_id": ANY,
            "handler": DOMAIN,
            "title": "test",
            "description": None,
            "description_placeholders": None,
            "result": ANY,
            "options": {},
            "data": {
                CONF_CLIMATE: True,
                CONF_DEVICE_ID: "deviceid",
                CONF_HOST: "hostname",
                CONF_LOCAL_KEY: "localkey",
                "lock_child_lock": False,
                CONF_TYPE: "kogan_kahtp_heater",
            },
        }
        assert expected == result


async def test_options_flow_init(hass):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_SWITCH: True,
            CONF_TYPE: "smartplugv1",
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
            CONF_SWITCH: True,
        }
    )


@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_modifies_config(mock_test, hass):
    mock_device = MagicMock()
    mock_test.return_value = mock_device

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        unique_id="uniqueid",
        data={
            CONF_CLIMATE: True,
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            "lock_child_lock": True,
            CONF_NAME: "test",
            CONF_TYPE: "kogan_kahtp_heater",
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
            CONF_CLIMATE: True,
            CONF_HOST: "new_hostname",
            CONF_LOCAL_KEY: "new_key",
            "lock_child_lock": False,
        },
    )
    expected = {
        CONF_CLIMATE: True,
        CONF_HOST: "new_hostname",
        CONF_LOCAL_KEY: "new_key",
        "lock_child_lock": False,
    }
    assert "create_entry" == result["type"]
    assert "" == result["title"]
    assert result["result"] is True
    assert expected == result["data"]


@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_fails_when_connection_fails(mock_test, hass):
    mock_test.return_value = None

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_SWITCH: True,
            CONF_TYPE: "smartplugv1",
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
            CONF_SWITCH: False,
        },
    )
    assert "form" == result["type"]
    assert "user" == result["step_id"]
    assert {"base": "connection"} == result["errors"]


@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_fails_when_config_is_missing(mock_test, hass):
    mock_device = MagicMock()
    mock_test.return_value = mock_device

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_SWITCH: True,
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


# More tests to exercise code branches that earlier tests missed.
@patch("custom_components.tuya_local.setup_device")
async def test_async_setup_entry_for_dehumidifier(mock_setup, hass):
    """Test setting up based on a config entry.  Repeats test_init_entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        unique_id="uniqueid",
        data={
            CONF_CLIMATE: False,
            CONF_DEVICE_ID: "deviceid",
            CONF_FAN: True,
            CONF_HOST: "hostname",
            CONF_HUMIDIFIER: True,
            CONF_LIGHT: True,
            CONF_LOCK: False,
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_TYPE: "dehumidifier",
        },
    )
    assert await async_setup_entry(hass, config_entry)


@patch("custom_components.tuya_local.setup_device")
async def test_async_setup_entry_for_switch(mock_device, hass):
    """Test setting up based on a config entry.  Repeats test_init_entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=6,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_SWITCH: True,
            CONF_TYPE: "smartplugv2",
        },
    )
    assert await async_setup_entry(hass, config_entry)
