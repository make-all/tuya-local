"""
Setup for different kinds of Tuya cover devices
"""
from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
import logging

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
        "cover",
        TuyaLocalCover,
    )


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
        self._position_dp = dps_map.pop("position", None)
        self._currentpos_dp = dps_map.pop("current_position", None)
        self._control_dp = dps_map.pop("control", None)
        self._action_dp = dps_map.pop("action", None)
        self._open_dp = dps_map.pop("open", None)
        self._reversed_dp = dps_map.pop("reversed", None)
        self._init_end(dps_map)

        self._support_flags = 0
        if self._position_dp:
            self._support_flags |= CoverEntityFeature.SET_POSITION
        if self._control_dp:
            if "stop" in self._control_dp.values(self._device):
                self._support_flags |= CoverEntityFeature.STOP
            if "open" in self._control_dp.values(self._device):
                self._support_flags |= CoverEntityFeature.OPEN
            if "close" in self._control_dp.values(self._device):
                self._support_flags |= CoverEntityFeature.CLOSE
        # Tilt not yet supported, as no test devices known

    @property
    def _is_reversed(self):
        return self._reversed_dp and self._reversed_dp.get_value(self._device)

    def _maybe_reverse(self, percent):
        """Reverse the percentage if it should be, otherwise leave it alone"""
        return 100 - percent if self._is_reversed else percent

    @property
    def device_class(self):
        """Return the class of ths device"""
        dclass = self._config.device_class
        try:
            return CoverDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(f"Unrecognised cover device class of {dclass} ignored")
            return None

    @property
    def supported_features(self):
        """Inform HA of the supported features."""
        return self._support_flags

    def _state_to_percent(self, state):
        """Convert a state to percent open"""
        if state == "opened":
            return 100
        elif state == "closed":
            return 0
        else:
            return 50

    @property
    def current_cover_position(self):
        """Return current position of cover."""
        if self._currentpos_dp:
            pos = self._currentpos_dp.get_value(self._device)
            if pos is not None:
                return self._maybe_reverse(pos)

        if self._position_dp:
            pos = self._position_dp.get_value(self._device)
            return self._maybe_reverse(pos)

        if self._open_dp:
            state = self._open_dp.get_value(self._device)
            if state is not None:
                return 100 if state else 0

        if self._action_dp:
            state = self._action_dp.get_value(self._device)
            return self._state_to_percent(state)

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        # If dps is available to inform current action, use that
        if self._action_dp:
            action = self._action_dp.get_value(self._device)
            if action is not None:
                return action == "opening"
        # Otherwise use last command and check it hasn't completed
        if self._control_dp:
            cmd = self._control_dp.get_value(self._device)
            pos = self.current_cover_position
            if pos is not None:
                return (
                    cmd != "close"
                    and cmd != "stop"
                    and self.current_cover_position < 95
                )

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        # If dps is available to inform current action, use that
        if self._action_dp:
            action = self._action_dp.get_value(self._device)
            if action is not None:
                return action == "closing"
        # Otherwise use last command and check it hasn't completed
        if self._control_dp:
            closed = self.is_closed
            cmd = self._control_dp.get_value(self._device)
            if closed is not None:
                return cmd != "open" and cmd != "stop" and not closed

    @property
    def is_closed(self):
        """Return if the cover is closed or not, if it can be determined."""
        # Only use position if it is reliable, otherwise curtain can become
        # stuck in "open" state when we don't actually know what state it is.
        pos = self.current_cover_position
        if isinstance(pos, int):
            return pos < 5

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        if self._control_dp and "open" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "open")
        elif self._position_dp:
            pos = self._maybe_reverse(100)
            await self._position_dp.async_set_value(self._device, pos)
        else:
            raise NotImplementedError()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        if self._control_dp and "close" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "close")
        elif self._position_dp:
            pos = self._maybe_reverse(0)
            await self._position_dp.async_set_value(self._device, pos)
        else:
            raise NotImplementedError()

    async def async_set_cover_position(self, position, **kwargs):
        """Set the cover to a specific position."""
        if position is None:
            raise AttributeError()
        if self._position_dp:
            position = self._maybe_reverse(position)
            await self._position_dp.async_set_value(self._device, position)
        else:
            raise NotImplementedError()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        if self._control_dp and "stop" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "stop")
        else:
            raise NotImplementedError()
