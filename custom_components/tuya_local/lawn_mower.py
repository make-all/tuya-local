"""
Setup for different kinds of Tuya lawn mowers
"""
from enum import IntFlag

from homeassistant.components.lawn_mower import LawnMowerEntity
from homeassistant.components.lawn_mower.const import (
    SERVICE_DOCK,
    SERVICE_PAUSE,
    SERVICE_START_MOWING,
    LawnMowerActivity,
)
from homeassistant.components.lawn_mower.const import (
    LawnMowerEntityFeature as BaseFeature,
)

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

SERVICE_FIXED_MOWING = "fixed_mowing"
SERVICE_CANCEL = "cancel"

class ExtendedLawnMowerEntityFeature(IntFlag):
    START_MOWING = BaseFeature.START_MOWING
    PAUSE = BaseFeature.PAUSE
    DOCK = BaseFeature.DOCK
    FIXED_MOWING = 8
    CANCEL = 16

async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "lawn_mower",
        TuyaLocalLawnMower,
    )



class TuyaLocalLawnMower(TuyaLocalEntity, LawnMowerEntity):
    """Representation of a Tuya Lawn Mower"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the lawn mower.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._activity_dp = dps_map.pop("activity", None)
        self._command_dp = dps_map.pop("command", None)
        self._init_end(dps_map)

        if self._command_dp:
            available_commands = self._command_dp.values(self._device)
            if SERVICE_START_MOWING in available_commands:
                self._attr_supported_features |= ExtendedLawnMowerEntityFeature.START_MOWING
            if SERVICE_PAUSE in available_commands:
                self._attr_supported_features |= ExtendedLawnMowerEntityFeature.PAUSE
            if SERVICE_DOCK in available_commands:
                self._attr_supported_features |= ExtendedLawnMowerEntityFeature.DOCK
            if SERVICE_FIXED_MOWING in available_commands:
                self._attr_supported_features |= ExtendedLawnMowerEntityFeature.FIXED_MOWING
            if SERVICE_CANCEL in available_commands:
                self._attr_supported_features |= ExtendedLawnMowerEntityFeature.CANCEL



    @property
    def activity(self) -> LawnMowerActivity | None:
        """Return the status of the lawn mower."""
        return LawnMowerActivity(self._activity_dp.get_value(self._device))

    async def async_start_mowing(self) -> None:
        """Start mowing the lawn."""
        if self._command_dp:
            await self._command_dp.async_set_value(self._device, SERVICE_START_MOWING)

    async def async_pause(self):
        """Pause lawn mowing."""
        if self._command_dp:
            await self._command_dp.async_set_value(self._device, SERVICE_PAUSE)

    async def async_dock(self):
        """Stop mowing and return to dock."""
        if self._command_dp:
            await self._command_dp.async_set_value(self._device, SERVICE_DOCK)

    async def async_fixed_mowing(self):
        """Start spot mowing."""
        if self._command_dp:
            await self._command_dp.async_set_value(self._device, SERVICE_FIXED_MOWING)

    async def async_cancel(self):
        """Cancel lawn mower ongoing task."""
        if self._command_dp:
            await self._command_dp.async_set_value(self._device, SERVICE_CANCEL)
            

