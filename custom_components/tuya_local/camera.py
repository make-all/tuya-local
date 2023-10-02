"""
Platform for Tuya Cameras
"""

import logging

from homeassistant.components.camera import Camera as CameraEntity
from homeassistant.components.camera import CameraEntityFeature

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "camera",
        TuyaLocalCamera,
    )


class TuyaLocalCamera(TuyaLocalEntity, CameraEntity):
    """Representation of a Tuya Camera"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the camera.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._switch_dp = dps_map.pop("switch", None)
        self._snapshot_dp = dps_map.pop("snapshot", None)
        self._record_dp = dps_map.pop("record", None)
        self._motion_enable_dp = dps_map.pop("motion_enable", None)

        self._init_end(dps_map)
        if self._switch_dp:
            self._attr_supported_features |= CameraEntityFeature.ON_OFF

    @property
    def is_recording(self):
        """Return whether the camera is recording, if we know that."""
        if self._record_dp:
            return self._record_dp.get_value(self._device)

    @property
    def motion_detection_enabled(self):
        """Return whether motion detection is enabled if supported."""
        if self._motion_enable_dp:
            return self._motion_enable_dp.get_value(self._device)

    async def async_camera_image(self, width=None, height=None):
        if self._snapshot_dp:
            return self._snapshot_dp.decoded_value(self._device)

    @property
    def is_on(self):
        """Return the power state of the camera"""
        if self._switch_dp:
            return self._switch_dp.get_value(self._device)

    async def async_turn_off(self):
        """Turn off the camera"""
        if not self._switch_dp:
            raise NotImplementedError()
        await self._switch_dp.async_set_value(self._device, False)

    async def async_turn_on(self):
        """Turn on the camera"""
        if not self._switch_dp:
            raise NotImplementedError()
        await self._switch_dp.async_set_value(self._device, True)

    async def async_enable_motion_detection(self):
        """Enable motion detection on the camera"""
        if not self._motion_enable_dp:
            raise NotImplementedError()
        await self._motion_enable_dp.async_set_value(self._device, True)

    async def async_disable_motion_detection(self):
        """Disable motion detection on the camera"""
        if not self._motion_enable_dp:
            raise NotImplementedError()
        await self._motion_enable_dp.async_set_value(self._device, False)
