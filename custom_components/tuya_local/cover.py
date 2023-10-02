"""
Setup for different kinds of Tuya cover devices
"""
import logging

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)

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
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._position_dp = dps_map.pop("position", None)
        self._currentpos_dp = dps_map.pop("current_position", None)
        self._control_dp = dps_map.pop("control", None)
        self._action_dp = dps_map.pop("action", None)
        self._open_dp = dps_map.pop("open", None)
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
    def device_class(self):
        """Return the class of ths device"""
        dclass = self._config.device_class
        try:
            return CoverDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(
                    "Unrecognised cover device class of %s ignored",
                    dclass,
                )
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
                return pos

        if self._position_dp:
            pos = self._position_dp.get_value(self._device)
            return pos

        if self._open_dp:
            state = self._open_dp.get_value(self._device)
            if state is not None:
                return 100 if state else 0

        if self._action_dp:
            state = self._action_dp.get_value(self._device)
            return self._state_to_percent(state)

    @property
    def _current_state(self):
        """Return the current state of the cover if it can be determined,
        or None if it is inconclusive.
        """
        if self._action_dp:
            action = self._action_dp.get_value(self._device)
            if action in ["opening", "closing", "opened", "closed"]:
                return action

        if self._currentpos_dp:
            pos = self._currentpos_dp.get_value(self._device)
            # we have a current pos dp, but it isn't telling us where the
            # curtain is... we can't tell the state.
            if pos is None:
                return None
            if pos < 5:
                return "closed"
            elif pos > 95:
                return "opened"
            if self._position_dp:
                setpos = self._position_dp.get_value(self._device)
                if setpos == pos:
                    # if the current position is around the set position,
                    # which is not closed, then we want is_closed to return
                    # false, so HA gets the full state from position.
                    return "opened"
        if self._control_dp:
            cmd = self._control_dp.get_value(self._device)
            pos = self.current_cover_position
            if pos is not None:
                if cmd == "open":
                    if pos > 95:
                        return "opened"
                    else:
                        return "opening"
                elif cmd == "close":
                    if pos < 5:
                        return "closed"
                    else:
                        return "closing"

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        state = self._current_state
        if state is None:
            # If we return false, and is_closing and is_opening are also false,
            # HA assumes open.  If we don't know, return None.
            return None
        else:
            return state == "opening"

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        state = self._current_state
        if state is None:
            # If we return false, and is_closing and is_opening are also false,
            # HA assumes open.  If we don't know, return None.
            return None
        else:
            return state == "closing"

    @property
    def is_closed(self):
        """Return if the cover is closed or not, if it can be determined."""
        pos = self.current_cover_position
        if pos is None:
            # If we return false, and is_closing and is_opening are also false,
            # HA assumes open.  If we don't know, return None.
            return None
        else:
            return pos == 0

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        if self._control_dp and "open" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "open")
        elif self._position_dp:
            pos = 100
            await self._position_dp.async_set_value(self._device, pos)
        else:
            raise NotImplementedError()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        if self._control_dp and "close" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "close")
        elif self._position_dp:
            pos = 0
            await self._position_dp.async_set_value(self._device, pos)
        else:
            raise NotImplementedError()

    async def async_set_cover_position(self, position, **kwargs):
        """Set the cover to a specific position."""
        if position is None:
            raise AttributeError()
        if self._position_dp:
            await self._position_dp.async_set_value(self._device, position)
        else:
            raise NotImplementedError()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        if self._control_dp and "stop" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "stop")
        else:
            raise NotImplementedError()
