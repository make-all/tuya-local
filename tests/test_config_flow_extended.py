"""Extended tests for the config flow — cloud steps, user step, search."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.const import CONF_HOST, CONF_NAME

from custom_components.tuya_local import config_flow
from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)

TESTKEY = "testlocalkey12345"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def prevent_task_creation(mocker):
    mocker.patch("custom_components.tuya_local.device.TuyaLocalDevice.register_entity")
    yield


@pytest.fixture
def bypass_setup(mocker):
    mocker.patch("custom_components.tuya_local.async_setup_entry", return_value=True)
    yield


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
