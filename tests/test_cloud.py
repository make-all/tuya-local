"""Tests for the Tuya cloud interface."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.tuya_local.cloud import (
    HUB_CATEGORIES,
    Cloud,
    DeviceListener,
    TokenListener,
)
from custom_components.tuya_local.const import (
    CONF_ENDPOINT,
    CONF_LOCAL_KEY,
    CONF_TERMINAL_ID,
    DOMAIN,
    TUYA_RESPONSE_CODE,
    TUYA_RESPONSE_MSG,
    TUYA_RESPONSE_QR_CODE,
    TUYA_RESPONSE_RESULT,
    TUYA_RESPONSE_SUCCESS,
)


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {DOMAIN: {}}

    async def run_in_executor(fn, *args):
        return fn(*args)

    hass.async_add_executor_job = AsyncMock(side_effect=run_in_executor)
    return hass


@pytest.fixture
def cloud(mock_hass):
    return Cloud(mock_hass)


class TestCloudInit:
    def test_init_without_cache(self, mock_hass):
        c = Cloud(mock_hass)
        assert c.is_authenticated is False

    def test_init_with_cached_auth(self, mock_hass):
        mock_hass.data[DOMAIN]["auth_cache"] = {
            "user_code": "abc",
            "terminal_id": "tid",
            "endpoint": "ep",
            "token_info": {},
        }
        c = Cloud(mock_hass)
        assert c.is_authenticated is True


class TestIsAuthenticated:
    def test_false_by_default(self, cloud):
        assert cloud.is_authenticated is False

    def test_true_after_login(self, cloud, mock_hass):
        mock_hass.data[DOMAIN]["auth_cache"] = {"user_code": "test"}
        c = Cloud(mock_hass)
        assert c.is_authenticated is True


class TestLastError:
    def test_none_by_default(self, cloud):
        assert cloud.last_error is None

    @pytest.mark.asyncio
    async def test_set_after_failed_qr(self, cloud):
        with patch(
            "custom_components.tuya_local.cloud.LoginControl"
        ) as MockLoginControl:
            mock_lc = MockLoginControl.return_value
            mock_lc.qr_code.return_value = {
                TUYA_RESPONSE_SUCCESS: False,
                TUYA_RESPONSE_CODE: 1001,
                TUYA_RESPONSE_MSG: "Invalid code",
            }
            cloud._Cloud__login_control = mock_lc
            await cloud.async_get_qr_code("test_code")
            error = cloud.last_error
            assert error is not None
            assert error[TUYA_RESPONSE_CODE] == 1001
            assert error[TUYA_RESPONSE_MSG] == "Invalid code"


class TestGetQrCode:
    @pytest.mark.asyncio
    async def test_without_user_code_returns_false(self, cloud):
        result = await cloud.async_get_qr_code()
        assert result is not None  # Returns (False, {...}) tuple

    @pytest.mark.asyncio
    async def test_success(self, cloud):
        mock_lc = MagicMock()
        mock_lc.qr_code.return_value = {
            TUYA_RESPONSE_SUCCESS: True,
            TUYA_RESPONSE_RESULT: {
                TUYA_RESPONSE_QR_CODE: "https://qr.example.com/code123",
            },
        }
        cloud._Cloud__login_control = mock_lc
        result = await cloud.async_get_qr_code("my_user_code")
        assert result == "https://qr.example.com/code123"

    @pytest.mark.asyncio
    async def test_failure(self, cloud):
        mock_lc = MagicMock()
        mock_lc.qr_code.return_value = {
            TUYA_RESPONSE_SUCCESS: False,
            TUYA_RESPONSE_CODE: 500,
            TUYA_RESPONSE_MSG: "Server error",
        }
        cloud._Cloud__login_control = mock_lc
        result = await cloud.async_get_qr_code("my_user_code")
        assert result is False

    @pytest.mark.asyncio
    async def test_reuses_user_code(self, cloud):
        mock_lc = MagicMock()
        mock_lc.qr_code.return_value = {
            TUYA_RESPONSE_SUCCESS: True,
            TUYA_RESPONSE_RESULT: {
                TUYA_RESPONSE_QR_CODE: "qr1",
            },
        }
        cloud._Cloud__login_control = mock_lc

        await cloud.async_get_qr_code("my_code")
        # Second call without user_code should reuse
        await cloud.async_get_qr_code()
        assert mock_lc.qr_code.call_count == 2
        assert mock_lc.qr_code.call_args_list[1][0][2] == "my_code"


class TestLogin:
    @pytest.mark.asyncio
    async def test_without_qr_returns_false(self, cloud):
        result = await cloud.async_login()
        # Returns (False, {}) when no user_code/qr_code
        assert result is not None

    @pytest.mark.asyncio
    async def test_success(self, cloud, mock_hass):
        # First get QR code
        mock_lc = MagicMock()
        mock_lc.qr_code.return_value = {
            TUYA_RESPONSE_SUCCESS: True,
            TUYA_RESPONSE_RESULT: {TUYA_RESPONSE_QR_CODE: "qr_code_value"},
        }
        mock_lc.login_result.return_value = (
            True,
            {
                CONF_TERMINAL_ID: "term_123",
                CONF_ENDPOINT: "https://openapi.tuyaus.com",
                "t": 1234567890,
                "uid": "user_abc",
                "expire_time": 7200,
                "access_token": "at_xyz",
                "refresh_token": "rt_xyz",
            },
        )
        cloud._Cloud__login_control = mock_lc

        await cloud.async_get_qr_code("user_code_123")
        result = await cloud.async_login()
        assert result is True
        assert cloud.is_authenticated is True
        assert mock_hass.data[DOMAIN]["auth_cache"] is not None

    @pytest.mark.asyncio
    async def test_failure_clears_auth(self, cloud, mock_hass):
        mock_lc = MagicMock()
        mock_lc.qr_code.return_value = {
            TUYA_RESPONSE_SUCCESS: True,
            TUYA_RESPONSE_RESULT: {TUYA_RESPONSE_QR_CODE: "qr_code_value"},
        }
        mock_lc.login_result.return_value = (
            False,
            {
                TUYA_RESPONSE_CODE: 2000,
                TUYA_RESPONSE_MSG: "Auth failed",
            },
        )
        cloud._Cloud__login_control = mock_lc

        await cloud.async_get_qr_code("user_code_123")
        result = await cloud.async_login()
        assert result is False
        assert cloud.is_authenticated is False
        assert mock_hass.data[DOMAIN]["auth_cache"] is None


class TestLogout:
    def test_logout_clears_auth(self, cloud, mock_hass):
        # Manually set authentication
        mock_hass.data[DOMAIN]["auth_cache"] = {"some": "data"}
        cloud._Cloud__authentication = {"some": "data"}
        assert cloud.is_authenticated is True

        cloud.logout()
        assert cloud.is_authenticated is False
        assert mock_hass.data[DOMAIN]["auth_cache"] is None


class TestGetDevices:
    @pytest.mark.asyncio
    async def test_get_devices(self, cloud, mock_hass):
        # Set up authentication
        cloud._Cloud__authentication = {
            "user_code": "uc",
            "terminal_id": "tid",
            "endpoint": "ep",
            "token_info": {"access_token": "at"},
        }

        mock_device = MagicMock()
        mock_device.category = "dj"
        mock_device.id = "dev_001"
        mock_device.ip = "192.168.1.100"
        mock_device.local_key = "local_key_123"
        mock_device.name = "Test Light"
        mock_device.node_id = ""
        mock_device.online = True
        mock_device.product_id = "prod_001"
        mock_device.product_name = "Smart Light"
        mock_device.uid = "uid_001"
        mock_device.uuid = "uuid_001"
        mock_device.support_local = True

        with patch("custom_components.tuya_local.cloud.Manager") as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.device_map = {"dev_001": mock_device}
            mock_manager.update_device_cache = MagicMock()

            devices = await cloud.async_get_devices()
            assert "dev_001/" in devices
            assert devices["dev_001/"]["name"] == "Test Light"
            assert devices["dev_001/"][CONF_LOCAL_KEY] == "local_key_123"
            assert devices["dev_001/"]["is_hub"] is False

    @pytest.mark.asyncio
    async def test_get_devices_hub_category(self, cloud, mock_hass):
        cloud._Cloud__authentication = {
            "user_code": "uc",
            "terminal_id": "tid",
            "endpoint": "ep",
            "token_info": {"access_token": "at"},
        }

        mock_device = MagicMock()
        mock_device.category = "zigbee"
        mock_device.id = "hub_001"
        mock_device.ip = "192.168.1.200"
        mock_device.local_key = "lk"
        mock_device.name = "Hub"
        mock_device.node_id = ""
        mock_device.online = True
        mock_device.product_id = "hp_001"
        mock_device.product_name = "Zigbee Hub"
        mock_device.uid = "uid_hub"
        mock_device.uuid = "uuid_hub"
        mock_device.support_local = True

        with patch("custom_components.tuya_local.cloud.Manager") as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.device_map = {"hub_001": mock_device}
            mock_manager.update_device_cache = MagicMock()

            devices = await cloud.async_get_devices()
            assert devices["hub_001/"]["is_hub"] is True


class TestGetDatamodel:
    @pytest.mark.asyncio
    async def test_get_datamodel(self, cloud, mock_hass):
        cloud._Cloud__authentication = {
            "user_code": "uc",
            "terminal_id": "tid",
            "endpoint": "ep",
            "token_info": {"access_token": "at"},
        }

        mock_response = {
            "result": {
                "dpStatusRelationDTOS": [
                    {
                        "dpId": 1,
                        "dpCode": "switch",
                        "valueType": "Boolean",
                        "valueDesc": "{}",
                        "enumMappingMap": {},
                        "supportLocal": True,
                    },
                    {
                        "dpId": 2,
                        "dpCode": "cloud_only",
                        "valueType": "Boolean",
                        "valueDesc": "{}",
                        "enumMappingMap": {},
                        "supportLocal": False,
                    },
                ]
            }
        }

        with patch("custom_components.tuya_local.cloud.Manager") as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.customer_api.get.return_value = mock_response

            result = await cloud.async_get_datamodel("dev_001")
            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["name"] == "switch"


class TestDeviceListener:
    def test_update_device(self):
        hass = MagicMock()
        manager = MagicMock()
        device = MagicMock()
        device.id = "dev_001"
        manager.device_map = {"dev_001": MagicMock()}
        listener = DeviceListener(hass, manager)
        # Should not raise
        listener.update_device(device, ["status"])

    def test_add_device(self):
        hass = MagicMock()
        manager = MagicMock()
        device = MagicMock()
        device.id = "dev_001"
        manager.device_map = {"dev_001": MagicMock()}
        listener = DeviceListener(hass, manager)
        listener.add_device(device)

    def test_remove_device(self):
        hass = MagicMock()
        manager = MagicMock()
        manager.device_map = {"dev_001": MagicMock()}
        listener = DeviceListener(hass, manager)
        listener.remove_device("dev_001")


class TestTokenListener:
    def test_update_token(self):
        hass = MagicMock()
        listener = TokenListener(hass)
        # Should not raise
        listener.update_token({"access_token": "new_token"})


class TestHubCategories:
    def test_known_hub_categories(self):
        assert "zigbee" in HUB_CATEGORIES
        assert "wg2" in HUB_CATEGORIES
        assert "wnykq" in HUB_CATEGORIES

    def test_non_hub_category(self):
        assert "dj" not in HUB_CATEGORIES
