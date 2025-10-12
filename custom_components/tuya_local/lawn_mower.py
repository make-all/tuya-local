"""
Setup for different kinds of Tuya lawn mowers
"""

import logging
from enum import IntFlag, StrEnum

from homeassistant.components.lawn_mower import LawnMowerEntity
from homeassistant.components.lawn_mower.const import (
    SERVICE_DOCK,
    SERVICE_PAUSE,
    SERVICE_START_MOWING,
)
from homeassistant.components.lawn_mower.const import (
    LawnMowerActivity as BaseActivity,
)
from homeassistant.components.lawn_mower.const import (
    LawnMowerEntityFeature as BaseFeature,
)

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)

SERVICE_FIXED_MOWING = "fixed_mowing"
SERVICE_CANCEL = "cancel"
SERVICE_RESUME = "resume"


class ExtendedLawnMowerActivity(StrEnum):
    """Extend Base Lawn Mower Activities of HA."""

    """Device is in error state, needs assistance."""
    ERROR = BaseActivity.ERROR

    """Paused during activity."""
    PAUSED = BaseActivity.PAUSED

    """Device is mowing."""
    MOWING = BaseActivity.MOWING

    """Device is docked, but not charging."""
    DOCKED = BaseActivity.DOCKED

    """Device is returning."""
    RETURNING = BaseActivity.RETURNING

    """Device is in standby/idle state."""
    STANDBY = "standby"

    """Device is charging."""
    CHARGING = "charging"

    """Device is stopped."""
    EMERGENCY = "manually stopped"

    """Device is Locked by the UI/cover opening"""
    LOCKED = "locked"

    """Device is returning to the docking station."""
    PARK = BaseActivity.RETURNING

    """Device is got an additional task but it is hanged until charged."""
    CHARGING_WITH_TASK_SUSPEND = "charging with queued task"

    """Device is mowing around a fixed spot."""
    FIXED_MOWING = "fixed mowing"


# Create a new flag that includes both base and extended features
class ExtendedLawnMowerEntityFeature(IntFlag):
    """Extended Lawn Mower Entity Features."""

    START_MOWING = BaseFeature.START_MOWING
    PAUSE = BaseFeature.PAUSE
    DOCK = BaseFeature.DOCK
    FIXED_MOWING = 8
    CANCEL = 16
    RESUME = 32

    @classmethod
    def from_base_features(cls, features: int) -> "ExtendedLawnMowerEntityFeature":
        """Convert base features to extended features."""
        return cls(features)


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

        # Initialize with no features
        self._attr_supported_features = 0

        if self._command_dp:
            if hasattr(self._command_dp, "values"):
                available_commands = self._command_dp.values(self._device)
                _LOGGER.debug(
                    "Raw available_commands: %s (type: %s)",
                    available_commands,
                    type(available_commands).__name__,
                )

                if not available_commands:
                    return

                # Map of command values to their corresponding feature flags
                command_to_feature = {
                    "start_mowing": ExtendedLawnMowerEntityFeature.START_MOWING,
                    "pause": ExtendedLawnMowerEntityFeature.PAUSE,
                    "dock": ExtendedLawnMowerEntityFeature.DOCK,
                    "fixed_mowing": ExtendedLawnMowerEntityFeature.FIXED_MOWING,
                    "cancel": ExtendedLawnMowerEntityFeature.CANCEL,
                    "resume": ExtendedLawnMowerEntityFeature.RESUME,
                }

                _LOGGER.debug("Command to feature mapping: %s", command_to_feature)

                # Set supported features based on available commands
                for command, feature in command_to_feature.items():
                    if command in available_commands:
                        self._attr_supported_features |= feature.value

                # Log the final features in a readable format
                features = []
                if (
                    self._attr_supported_features
                    & ExtendedLawnMowerEntityFeature.START_MOWING
                ):
                    features.append(ExtendedLawnMowerEntityFeature.START_MOWING.name)
                if self._attr_supported_features & ExtendedLawnMowerEntityFeature.PAUSE:
                    features.append(ExtendedLawnMowerEntityFeature.PAUSE.name)
                if self._attr_supported_features & ExtendedLawnMowerEntityFeature.DOCK:
                    features.append(ExtendedLawnMowerEntityFeature.DOCK.name)
                if (
                    self._attr_supported_features
                    & ExtendedLawnMowerEntityFeature.FIXED_MOWING
                ):
                    features.append(ExtendedLawnMowerEntityFeature.FIXED_MOWING.name)
                if (
                    self._attr_supported_features
                    & ExtendedLawnMowerEntityFeature.CANCEL
                ):
                    features.append(ExtendedLawnMowerEntityFeature.CANCEL.name)
                if (
                    self._attr_supported_features
                    & ExtendedLawnMowerEntityFeature.RESUME
                ):
                    features.append(ExtendedLawnMowerEntityFeature.RESUME.name)

                _LOGGER.debug(
                    "Enabled features: %s", ", ".join(features) if features else "None"
                )

    @property
    def activity(self) -> ExtendedLawnMowerActivity | None:
        """Return the status of the lawn mower."""
        return ExtendedLawnMowerActivity(self._activity_dp.get_value(self._device))

    async def async_start_mowing(self) -> None:
        """Start mowing the lawn."""
        if self._command_dp:
            _LOGGER.debug("Starting mowing...")
            await self._command_dp.async_set_value(self._device, SERVICE_START_MOWING)

    async def async_pause(self):
        """Pause lawn mowing."""
        if self._command_dp:
            _LOGGER.debug("Pausing mowing...")
            await self._command_dp.async_set_value(self._device, SERVICE_PAUSE)

    async def async_dock(self):
        """Stop mowing and return to dock."""
        if self._command_dp:
            _LOGGER.debug("Returning to dock...")
            await self._command_dp.async_set_value(self._device, SERVICE_DOCK)

    async def async_fixed_mowing(self):
        """Start spot mowing."""
        if self._command_dp:
            _LOGGER.debug("Fixed mowing started...")
            await self._command_dp.async_set_value(self._device, "StartFixedMowing")

    async def async_cancel(self):
        """Cancel ongoing task."""
        if self._command_dp:
            _LOGGER.debug("Canceling ongoing task...")
            await self._command_dp.async_set_value(self._device, "CancelWork")

    async def async_resume(self):
        """Continue ongoing task."""
        if self._command_dp:
            _LOGGER.debug("Resuming ongoing task...")
            await self._command_dp.async_set_value(self._device, "ContinueWork")
