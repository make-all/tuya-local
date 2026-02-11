"""
Setup for different kinds of Tuya lock devices
"""

from base64 import b64encode

from homeassistant.components.lock import LockEntity, LockEntityFeature

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

# Remote Code unlocking protocol: 8 digit code set when paired by
# remote_no_pd_setkey (typically dp 60), user can obtain by
# eavesdropping cloud unlock messages.
# Format in case this command can be supported outside of pairing process:
# Request: Validity (1 byte 0 or 1), Member ID (2 bytes),
#  Start time (4 byte unixtime), End time (4 byte unixtime),
#  Usable times (2 bytes, 0=infinite), Key (8 bytes ASCII)

# Same 8 digit ASCII code used along with binary member ID to generate
# unlock command with remote_no_dp_key (typically dp 61)
# Locking usually possible without code, but remote_no_dp_key seems
# to also support locking with code.

# Request: action (1 byte), Member (2 bytes 0-100), code (8 bytes ASCII),
#    source (2 bytes)
CODE_LOCK = 0x00
CODE_UNLOCK = 0x01

CODE_SRC_UNKNOWN = 0x0000
CODE_SRC_APP = 0x0001
CODE_SRC_VOICE = 0x0002

# Reply: status (1 byte), Member ID (2 bytes 1 - 100)
CODE_REPLY_SUCCESS = 0x00
CODE_REPLY_FAIL = 0x01
CODE_REPLY_PWD_ERROR = 0x02
CODE_REPLY_TIMEOUT = 0x03
CODE_REPLY_OUTOFHOURS = 0x04
CODE_REPLY_WRONGCODE = 0x05
CODE_REPLY_DOUBLELOCKED = 0x06


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "lock",
        TuyaLocalLock,
    )


class TuyaLocalLock(TuyaLocalEntity, LockEntity):
    """Representation of a Tuya Wi-Fi connected lock."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the lock.
        Args:
          device (TuyaLocalDevice): The device API instance.
          config (TuyaEntityConfig): The configuration for this entity.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._lock_dp = dps_map.pop("lock", None)
        self._lock_state_dp = dps_map.pop("lock_state", None)
        self._open_dp = dps_map.pop("open", None)
        self._unlock_fp_dp = dps_map.pop("unlock_fingerprint", None)
        self._unlock_pw_dp = dps_map.pop("unlock_password", None)
        self._unlock_tmppw_dp = dps_map.pop("unlock_temp_pwd", None)
        self._unlock_dynpw_dp = dps_map.pop("unlock_dynamic_pwd", None)
        self._unlock_offlinepw_dp = dps_map.pop("unlock_offline_pwd", None)
        self._unlock_card_dp = dps_map.pop("unlock_card", None)
        self._unlock_app_dp = dps_map.pop("unlock_app", None)
        self._unlock_key_dp = dps_map.pop("unlock_key", None)
        self._unlock_ble_dp = dps_map.pop("unlock_ble", None)
        self._unlock_voice_dp = dps_map.pop("unlock_voice", None)
        self._unlock_face_dp = dps_map.pop("unlock_face", None)
        self._unlock_multi_dp = dps_map.pop("unlock_multi", None)
        self._unlock_ibeacon_dp = dps_map.pop("unlock_ibeacon", None)
        self._req_unlock_dp = dps_map.pop("request_unlock", None)
        self._approve_unlock_dp = dps_map.pop("approve_unlock", None)
        self._code_unlock_dp = dps_map.pop("code_unlock", None)
        self._req_intercom_dp = dps_map.pop("request_intercom", None)
        self._approve_intercom_dp = dps_map.pop("approve_intercom", None)
        self._jam_dp = dps_map.pop("jammed", None)
        self._init_end(dps_map)
        if self._open_dp and not self._open_dp.readonly:
            self._attr_supported_features = LockEntityFeature.OPEN

    @property
    def is_locked(self):
        """Return the a boolean representing whether the lock is locked."""
        lock = None
        if self._lock_state_dp:
            lock = self._lock_state_dp.get_value(self._device)
        if lock is None and self._lock_dp:
            lock = self._lock_dp.get_value(self._device)
        if lock is None:
            for d in (
                self._unlock_card_dp,
                self._unlock_dynpw_dp,
                self._unlock_fp_dp,
                self._unlock_offlinepw_dp,
                self._unlock_pw_dp,
                self._unlock_tmppw_dp,
                self._unlock_app_dp,
                self._unlock_key_dp,
                self._unlock_ble_dp,
                self._unlock_voice_dp,
                self._unlock_face_dp,
                self._unlock_multi_dp,
                self._unlock_ibeacon_dp,
            ):
                if d:
                    if d.get_value(self._device):
                        lock = False
                    elif lock is None:
                        lock = True
        return lock

    @property
    def is_open(self):
        if self._open_dp:
            return self._open_dp.get_value(self._device)

    @property
    def is_jammed(self):
        if self._jam_dp:
            return self._jam_dp.get_value(self._device)

    @property
    def code_format(self):
        """Return the code format of the lock."""
        if self._code_unlock_dp:
            return r".{8}"
        return None

    def unlocker_id(self, dp, type):
        if dp:
            unlock = dp.get_value(self._device)
            if unlock:
                if unlock is True:
                    return f"{type}"
                else:
                    return f"{type} #{unlock}"

    @property
    def changed_by(self):
        for dp, desc in {
            self._unlock_app_dp: "App",
            self._unlock_ble_dp: "Bluetooth",
            self._unlock_card_dp: "Card",
            self._unlock_dynpw_dp: "Dynamic Password",
            self._unlock_fp_dp: "Finger",
            self._unlock_key_dp: "Key",
            self._unlock_offlinepw_dp: "Offline Password",
            self._unlock_pw_dp: "Password",
            self._unlock_tmppw_dp: "Temporary Password",
            self._unlock_voice_dp: "Voice",
            self._unlock_face_dp: "Face",
            self._unlock_multi_dp: "Multifactor",
            self._unlock_ibeacon_dp: "iBeacon",
        }.items():
            by = self.unlocker_id(dp, desc)
            if by:
                # clear non-persistent dps immediately on reporting, instead
                # of waiting for the next poll, to make the lock more responsive
                # to multiple attempts
                if not dp.persist:
                    self._device._cached_state.pop(dp.id, None)
                return by

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        if self._lock_dp and not self._lock_dp.readonly:
            await self._lock_dp.async_set_value(self._device, True)
        elif self._code_unlock_dp:
            code = kwargs.get("code")
            if not code:
                raise ValueError("Code required to lock")
            msg = self.build_code_unlock_msg(
                CODE_LOCK, member_id=1, code=code, source=CODE_SRC_UNKNOWN
            )
            await self._code_unlock_dp.async_set_value(self._device, msg)
        else:
            raise NotImplementedError()

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        if self._code_unlock_dp:
            code = kwargs.get("code")
            if not code:
                raise ValueError("Code required to unlock")
            msg = self.build_code_unlock_msg(
                CODE_UNLOCK, member_id=1, code=code, source=CODE_SRC_UNKNOWN
            )
            await self._code_unlock_dp.async_set_value(self._device, msg)
        elif self._lock_dp and not self._lock_dp.readonly:
            await self._lock_dp.async_set_value(self._device, False)
        elif self._approve_unlock_dp:
            if self._req_unlock_dp and not self._req_unlock_dp.get_value(self._device):
                raise TimeoutError()
            await self._approve_unlock_dp.async_set_value(self._device, True)
        elif self._approve_intercom_dp:
            if self._req_intercom_dp and not self._req_intercom_dp.get_value(
                self._device
            ):
                raise TimeoutError()
            await self._approve_intercom_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_open(self, **kwargs):
        """Open the door latch."""
        if self._open_dp:
            await self._open_dp.async_set_value(self._device, True)

    def build_code_unlock_msg(self, action, member_id, code, source=CODE_SRC_UNKNOWN):
        """Generate the unlock code message."""
        if len(code) != 8 or not code.isascii():
            raise ValueError("Code must be 8 ASCII characters")
        msg = bytearray()
        msg.append(action)
        msg += member_id.to_bytes(2, "big")
        msg += code.encode("ascii")
        msg += source.to_bytes(2, "big")
        # msg += b"\x00"  # ordinary user (0x01 is admin)
        return b64encode(msg).decode("utf-8")
