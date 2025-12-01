from base64 import b64encode

from ..const import AILRINNI_FINGERPRINTLOCK_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

BATTERY_DP = "8"
UNLOCK_FP_DP = "12"
UNLOCK_PWD_DP = "13"
UNLOCK_DYN_DP = "14"
UNLOCK_BLE_DP = "19"
ALERT_DP = "21"
VOLUME_DP = "31"
LOCK_STATE_DP = "47"
TMPPW_CREATE_DP = "51"
TMPPW_DELETE_DP = "52"
TMPPW_MODIFY_DP = "53"
UNLOCK_TMP_DP = "55"
CODESET_DP = "60"
CODE_UNLOCK_DP = "61"
UNLOCK_APP_DP = "62"
UNLOCK_VOICE_DP = "63"
UNLOCK_OFFLINE_DP = "67"


class TestAilrinniFingerprintLock(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "ailrinni_fingerprint_lock.yaml", AILRINNI_FINGERPRINTLOCK_PAYLOAD
        )
        self.subject = self.entities.get("lock")
        self.mark_secondary(
            [
                "sensor_alert",
                "number_lock_volume",
                "text_remote_unlock_code",
                "text_new_credential",
                "text_delete_credential",
                "text_modify_credential",
                "text_new_temp_password",
                "text_delete_temp_password",
                "text_modify_temp_password",
                "text_sync_credentials",
                "text_offline_password_timestamp",
                "sensor_used_offline_password",
                "sensor_cleared_offline_passwords",
            ]
        )

    async def test_lock(self):
        """Test locking the lock."""
        expected = b64encode(
            b"\x00\x00\x01" + b"12345678" + b"\x00\x00",
        ).decode("utf-8")
        async with assert_device_properties_set(
            self.subject._device,
            {CODE_UNLOCK_DP: expected},
        ):
            await self.subject.async_lock(code="12345678")

    async def test_unlock(self):
        """Test unlocking the lock."""
        expected = b64encode(
            b"\x01\x00\x01" + b"12345678" + b"\x00\x00",
        ).decode("utf-8")
        async with assert_device_properties_set(
            self.subject._device,
            {CODE_UNLOCK_DP: expected},
        ):
            await self.subject.async_unlock(code="12345678")
