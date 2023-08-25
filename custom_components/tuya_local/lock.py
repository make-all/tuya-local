"""
Setup for different kinds of Tuya lock devices
"""
from homeassistant.components.lock import LockEntity

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity


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
        self._req_unlock_dp = dps_map.pop("request_unlock", None)
        self._approve_unlock_dp = dps_map.pop("approve_unlock", None)
        self._req_intercom_dp = dps_map.pop("request_intercom", None)
        self._approve_intercom_dp = dps_map.pop("approve_intercom", None)
        self._jam_dp = dps_map.pop("jammed", None)
        self._init_end(dps_map)

    @property
    def is_locked(self):
        """Return the a boolean representing whether the lock is locked."""
        lock = None
        if self._lock_dp:
            lock = self._lock_dp.get_value(self._device)
        else:
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
            ):
                if d:
                    if d.get_value(self._device):
                        lock = False
                    elif lock is None:
                        lock = True
        return lock

    @property
    def is_jammed(self):
        if self._jam_dp:
            return self._jam_dp.get_value(self._device)

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
        }.items():
            by = self.unlocker_id(dp, desc)
            if by:
                return by

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        if self._lock_dp:
            await self._lock_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        if self._lock_dp:
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
