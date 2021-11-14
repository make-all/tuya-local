"""
Platform to control tuya cover devices.
"""
import logging

from homeassistant.components.cover import (
    CoverEntity,
    DEVICE_CLASSES,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


class TuyaLocalCover(TuyaLocalEntity, CoverEntity):
    """Representation of a Tuya Cover Entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the cover device.
        Args:
          device (TuyaLocalDevice): The device API instance
          config (TuyaEntityConfig): The entity config
        """
        dps_map = self._init_begin(device, config)
        self._position_dps = dps_map.pop("position", None)
        self._control_dps = dps_map.pop("control", None)
        self._action_dps = dps_map.pop("action", None)
        self._open_dps = dps_map.pop("open", None)

        self._init_end(dps_map)

        self._support_flags = 0
        if self._position_dps:
            self._support_flags |= SUPPORT_SET_POSITION
        if self._control_dps:
            if "stop" in self._control_dps.values(self._device):
                self._support_flags |= SUPPORT_STOP
            if "open" in self._control_dps.values(self._device):
                self._support_flags |= SUPPORT_OPEN
            if "close" in self._control_dps.values(self._device):
                self._support_flags |= SUPPORT_CLOSE
        # Tilt not yet supported, as no test devices known

    @property
    def device_class(self):
        """Return the class of ths device"""
        dclass = self._config.device_class
        if dclass in DEVICE_CLASSES:
            return dclass
        else:
            return None

    @property
    def supported_features(self):
        """Inform HA of the supported features."""
        return self._support_flags

    @property
    def current_cover_position(self):
        """Return current position of cover."""
        if self._position_dps:
            return self._position_dps.get_value(self._device)

        if self._open_dps:
            state = self._open_dps.get_value(self._device)
            if state is not None:
                return 100 if state else 0

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        # If dps is available to inform current action, use that
        if self._action_dps:
            return self._action_dps.get_value(self._device) == "opening"
        # Otherwise use last command and check it hasn't completed
        if self._control_dps:
            return (
                self._control_dps.get_value(self._device) == "open"
                and self.current_cover_position != 100
            )

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        # If dps is available to inform current action, use that
        if self._action_dps:
            return self._action_dps.get_value(self._device) == "closing"
        # Otherwise use last command and check it hasn't completed
        if self._control_dps:
            return (
                self._control_dps.get_value(self._device) == "close"
                and not self.is_closed
            )

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        return self.current_cover_position == 0

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        if self._control_dps and "open" in self._control_dps.values(self._device):
            await self._control_dps.async_set_value(self._device, "open")
        elif self._position_dps:
            await self._position_dps.async_set_value(self._device, 100)
        else:
            raise NotImplementedError()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        if self._control_dps and "close" in self._control_dps.values(self._device):
            await self._control_dps.async_set_value(self._device, "close")
        elif self._position_dps:
            await self._position_dps.async_set_value(self._device, 0)
        else:
            raise NotImplementedError()

    async def async_set_cover_position(self, position, **kwargs):
        """Set the cover to a specific position."""
        if position is None:
            raise AttributeError()
        if self._position_dps:
            await self._position_dps.async_set_value(self._device, position)
        else:
            raise NotImplementedError()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        if self._control_dps and "stop" in self._control_dps.values(self._device):
            await self._control_dps.async_set_value(self._device, "stop")
        else:
            raise NotImplementedError()
