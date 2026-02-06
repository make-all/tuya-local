"""
Setup for different kinds of Tuya cover devices
"""

import logging
import asyncio
from datetime import datetime, timedelta

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

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
        self._tiltpos_dp = dps_map.pop("tilt_position", None)
        self._control_dp = dps_map.pop("control", None)
        self._action_dp = dps_map.pop("action", None)
        self._open_dp = dps_map.pop("open", None)
        self._init_end(dps_map)
        # Variabili per tracciare comandi e posizione target
        self._last_command = None
        self._target_position = None
        self._last_position = None  # Aggiungi per tracciare cambiamenti
        self._command_time = None   # Aggiungi per timeout
        self._position_stable_count = 0  # Conta quante volte la posizione è rimasta stabile

        self._support_flags = CoverEntityFeature(0)
        if self._position_dp:
            self._support_flags |= CoverEntityFeature.SET_POSITION
        if self._control_dp:
            if "stop" in self._control_dp.values(self._device):
                self._support_flags |= CoverEntityFeature.STOP
            if "open" in self._control_dp.values(self._device):
                self._support_flags |= CoverEntityFeature.OPEN
            if "close" in self._control_dp.values(self._device):
                self._support_flags |= CoverEntityFeature.CLOSE
        if self._tiltpos_dp:
            self._support_flags |= CoverEntityFeature.SET_TILT_POSITION

        # Open/close/stop tilt not yet supported, as no test devices known

    @property
    def device_class(self):
        """Return the class of ths device"""
        dclass = self._config.device_class
        try:
            return CoverDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(
                    "%s/%s: Unrecognised cover device class of %s ignored",
                    self._config._device.config,
                    self.name or "cover",
                    dclass,
                )

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

        if self._open_dp:
            state = self._open_dp.get_value(self._device)
            if state is not None:
                return 100 if state else 0

        if self._action_dp:
            state = self._action_dp.get_value(self._device)
            if state is not None:
                return self._state_to_percent(state)

        if self._position_dp:
            pos = self._position_dp.get_value(self._device)
            return pos

    @property
    def current_cover_tilt_position(self):
        """Return current tilt position of cover."""
        if self._tiltpos_dp:
            r = self._tiltpos_dp.range(self._device)
            val = self._tiltpos_dp.get_value(self._device)
            if r and val is not None:
                return ranged_value_to_percentage(r, val)
            return val

    def _reset_movement_state(self):
        """Reset movement tracking variables."""
        self._last_command = None
        self._target_position = None
        self._command_time = None
        self._position_stable_count = 0

    @property
    def _current_state(self):
        """Return the current state of the cover if it can be determined,
        or None if it is inconclusive.
        """
        if self._action_dp:
            action = self._action_dp.get_value(self._device)
            if action in ["opening", "closing", "opened", "closed"]:
                return action

        pos = self.current_cover_position
        if pos is None:
            if self._last_command == "opening":
                return "opening"
            elif self._last_command == "closing":
                return "closing"
            return None

        # Controlla timeout (30 secondi massimo per qualsiasi movimento)
        if self._command_time is not None:
            elapsed = datetime.now().timestamp() - self._command_time
            if elapsed > 30:  # Timeout dopo 30 secondi
                _LOGGER.debug(f"Cover movement timeout after {elapsed} seconds, resetting state")
                self._reset_movement_state()
                if pos < 5:
                    return "closed"
                else:
                    return "opened"

        # Controlla se la posizione è stabile (non cambia più)
        if self._last_command:
            if self._last_position is not None:
                if abs(pos - self._last_position) < 1:
                    # Posizione non è cambiata
                    self._position_stable_count += 1
                    # Se la posizione è stabile per 3 controlli consecutivi, il movimento è finito
                    if self._position_stable_count >= 3:
                        _LOGGER.debug(f"Position stable at {pos}, movement complete")
                        self._reset_movement_state()
                        if pos < 5:
                            return "closed"
                        else:
                            return "opened"
                else:
                    # Posizione sta cambiando, resetta il contatore
                    self._position_stable_count = 0
                    _LOGGER.debug(f"Position changed from {self._last_position} to {pos}")

            # Aggiorna ultima posizione
            self._last_position = pos

            # Controlla se abbiamo raggiunto il target
            if self._target_position is not None:
                if abs(pos - self._target_position) < 3:
                    _LOGGER.debug(f"Target position {self._target_position} reached at {pos}")
                    self._reset_movement_state()
                    if pos < 5:
                        return "closed"
                    else:
                        return "opened"

            # Ancora in movimento
            return self._last_command

        # Controlla gli estremi
        if pos < 5:
            return "closed"
        elif pos > 95:
            return "opened"

        if self._currentpos_dp and self._position_dp:
            setpos = self._position_dp.get_value(self._device)
            if setpos is not None and abs(setpos - pos) < 5:
                return "opened"

            if self._control_dp:
                cmd = self._control_dp.get_value(self._device)
                if cmd == "open":
                    return "opening"
                elif cmd == "close":
                    return "closing"

        return "opened"
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
        state = self._current_state
        if state is None:
            # If we return false, and is_closing and is_opening are also false,
            # HA assumes open.  If we don't know, return None.
            return None
        else:
            return state == "closed"

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        self._last_command = "opening"
        self._target_position = 100
        self._last_position = self.current_cover_position
        self._command_time = datetime.now().timestamp()
        self._position_stable_count = 0

        if self._control_dp and "open" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "open")
        elif self._position_dp:
            await self._position_dp.async_set_value(self._device, 100)
        elif self._currentpos_dp:
            await self._currentpos_dp.async_set_value(self._device, 100)
        else:
            raise NotImplementedError()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        self._last_command = "closing"
        self._target_position = 0
        self._last_position = self.current_cover_position
        self._command_time = datetime.now().timestamp()
        self._position_stable_count = 0

        if self._control_dp and "close" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "close")
        elif self._position_dp:
            await self._position_dp.async_set_value(self._device, 0)
        elif self._currentpos_dp:
            await self._currentpos_dp.async_set_value(self._device, 0)
        else:
            raise NotImplementedError()

    async def async_set_cover_position(self, position, **kwargs):
        """Set the cover to a specific position."""
        if position is None:
            raise AttributeError()

        current_pos = self.current_cover_position

        # Determina la direzione del movimento
        if current_pos is not None:
            if position > current_pos + 2:
                self._last_command = "opening"
                self._target_position = position
                self._last_position = current_pos
                self._command_time = datetime.now().timestamp()
                self._position_stable_count = 0
            elif position < current_pos - 2:
                self._last_command = "closing"
                self._target_position = position
                self._last_position = current_pos
                self._command_time = datetime.now().timestamp()
                self._position_stable_count = 0
            else:
                # Già nella posizione corretta
                self._reset_movement_state()

        if self._position_dp:
            await self._position_dp.async_set_value(self._device, position)
        elif self._currentpos_dp:
            await self._currentpos_dp.async_set_value(self._device, position)
        else:
            raise NotImplementedError()

    async def async_set_cover_tilt_position(self, tilt_position, **kwargs):
        """Set the cover tilt position."""
        if self._tiltpos_dp:
            if self._tiltpos_dp.values(self._device):
                tilt_position = min(
                    self._tiltpos_dp.values(self._device),
                    key=lambda x: abs(x - tilt_position),
                )
            elif self._tiltpos_dp.range(self._device):
                r = self._tiltpos_dp.range(self._device)
                tilt_position = percentage_to_ranged_value(r, tilt_position)

            await self._tiltpos_dp.async_set_value(self._device, tilt_position)
        else:
            raise NotImplementedError

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self._reset_movement_state()

        if self._control_dp and "stop" in self._control_dp.values(self._device):
            await self._control_dp.async_set_value(self._device, "stop")
        else:
            raise NotImplementedError()
