"""
Implementation of the Tuya media player devices
"""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Tuya Local media player platform."""
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "media_player",
        TuyaLocalMediaPlayer,
    )


class TuyaLocalMediaPlayer(TuyaLocalEntity, MediaPlayerEntity):
    """Representation of a Tuya Local media player device."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """Initialize the media player device."""
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._power_dp = dps_map.pop("switch", None)
        self._volume_dp = dps_map.pop("volume", None)
        self._mute_dp = dps_map.pop("mute", None)
        self._source_dp = dps_map.pop("source", None)
        self._state_dp = dps_map.pop("playback_state", None)
        self._play_dp = dps_map.pop("play", None)
        self._pause_dp = dps_map.pop("pause", None)
        self._prev_dp = dps_map.pop("prev", None)
        self._next_dp = dps_map.pop("next", None)
        self._stop_dp = dps_map.pop("stop", None)
        self._seek_dp = dps_map.pop("seek_position", None)
        self._clear_playlist_dp = dps_map.pop("clear_playlist", None)
        self._shuffle_dp = dps_map.pop("shuffle", None)
        self._repeat_dp = dps_map.pop("repeat", None)
        self._sound_mode_dp = dps_map.pop("sound_mode", None)
        self._init_end(dps_map)

        self._support_flags = MediaPlayerEntityFeature(0)
        if self._pause_dp:
            self._support_flags |= MediaPlayerEntityFeature.PAUSE
        if self._seek_dp:
            self._support_flags |= MediaPlayerEntityFeature.SEEK
        if self._volume_dp:
            self._support_flags |= MediaPlayerEntityFeature.VOLUME_SET
            if self._volume_dp.step is not None:
                self._support_flags |= MediaPlayerEntityFeature.VOLUME_STEP
        if self._mute_dp:
            self._support_flags |= MediaPlayerEntityFeature.VOLUME_MUTE
        if self._prev_dp:
            self._support_flags |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if self._next_dp:
            self._support_flags |= MediaPlayerEntityFeature.NEXT_TRACK
        if self._power_dp:
            self._support_flags |= MediaPlayerEntityFeature.TURN_ON
            self._support_flags |= MediaPlayerEntityFeature.TURN_OFF
        # PLAY_MEDIA for playing arbitrary media
        if self._source_dp:
            self._support_flags |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._stop_dp:
            self._support_flags |= MediaPlayerEntityFeature.STOP
        if self._clear_playlist_dp:
            self._support_flags |= MediaPlayerEntityFeature.CLEAR_PLAYLIST
        if self._play_dp:
            self._support_flags |= MediaPlayerEntityFeature.PLAY
        if self._shuffle_dp:
            self._support_flags |= MediaPlayerEntityFeature.SHUFFLE_SET
        if self._repeat_dp:
            self._support_flags |= MediaPlayerEntityFeature.REPEAT_SET
        if self._sound_mode_dp:
            self._support_flags |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
        # BROWSE_MEDIA for browsing media on the device
        # GROUPING for grouping multiple media players together
        # MEDIA_ANNOUNCE for sending TTS to the device
        # MEDIA_ENQUEUE for adding media to the queue
        # SEARCH_MEDIA for searching media on the device

    def state(self):
        """Return the state of the media player."""
        if self._state_dp:
            return self._state_dp.get_value(self._device)
        elif self._play_dp and self._play_dp.get_value(self._device):
            return MediaPlayerState.PLAYING
        elif self._pause_dp and self._pause_dp.get_value(self._device):
            return MediaPlayerState.PAUSED
        elif self._power_dp and not self._power_dp.get_value(self._device):
            return MediaPlayerState.OFF
        elif self._power_dp and self._power_dp.get_value(self._device):
            return MediaPlayerState.ON
        return None

    def volume_level(self):
        """Return the volume level of the media player (0..1)."""
        if self._volume_dp:
            return self._volume_dp.get_value(self._device)
        return None

    def volume_step(self):
        """Return the volume step of the media player."""
        if self._volume_dp:
            return self._volume_dp.step(self._device)
        return None

    def is_volume_muted(self):
        """Return True if the volume is muted."""
        if self._mute_dp:
            return self._mute_dp.get_value(self._device)
        return None

    def source(self):
        """Return the current input source of the media player."""
        if self._source_dp:
            return self._source_dp.get_value(self._device)
        return None

    def source_list(self):
        """Return the list of available input sources of the media player."""
        if self._source_dp:
            return self._source_dp.values(self._device)
        return None

    def sound_mode(self):
        """Return the current sound mode of the media player."""
        if self._sound_mode_dp:
            return self._sound_mode_dp.get_value(self._device)
        return None

    def sound_mode_list(self):
        """Return the list of available sound modes of the media player."""
        if self._sound_mode_dp:
            return self._sound_mode_dp.values(self._device)
        return None

    def shuffle(self):
        """Return the current shuffle state of the media player."""
        if self._shuffle_dp:
            return self._shuffle_dp.get_value(self._device)
        return None

    def repeat(self):
        """Return the current repeat state of the media player."""
        if self._repeat_dp:
            return self._repeat_dp.get_value(self._device)
        return None

    async def async_turn_on(self):
        """Turn on the media player."""
        if self._power_dp:
            await self._power_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_turn_off(self):
        """Turn off the media player."""
        if self._power_dp:
            await self._power_dp.async_set_value(self._device, False)
        else:
            raise NotImplementedError()

    async def async_mute_volume(self, mute):
        """Mute the volume."""
        if self._mute_dp:
            await self._mute_dp.async_set_value(self._device, mute)
        else:
            raise NotImplementedError()

    async def async_set_volume_level(self, volume):
        """Set the volume level."""
        if self._volume_dp:
            await self._volume_dp.async_set_value(self._device, volume)
        else:
            raise NotImplementedError()

    async def async_media_play(self):
        """Send play command."""
        if self._play_dp:
            await self._play_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_media_pause(self):
        """Send pause command."""
        if self._pause_dp:
            await self._pause_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_media_stop(self):
        """Send stop command."""
        if self._stop_dp:
            await self._stop_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_media_previous_track(self):
        """Send previous track command."""
        if self._prev_dp:
            await self._prev_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_media_next_track(self):
        """Send next track command."""
        if self._next_dp:
            await self._next_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_media_seek(self, position):
        """Seek to a specific position in the media."""
        if self._seek_dp:
            await self._seek_dp.async_set_value(self._device, position)
        else:
            raise NotImplementedError()

    async def async_select_source(self, source):
        """Select input source."""
        if self._source_dp:
            await self._source_dp.async_set_value(self._device, source)
        else:
            raise NotImplementedError()

    async def async_select_sound_mode(self, sound_mode):
        """Select sound mode."""
        if self._sound_mode_dp:
            await self._sound_mode_dp.async_set_value(self._device, sound_mode)
        else:
            raise NotImplementedError()

    async def async_clear_playlist(self):
        """Clear the playlist."""
        if self._clear_playlist_dp:
            await self._clear_playlist_dp.async_set_value(self._device, True)
        else:
            raise NotImplementedError()

    async def async_set_shuffle(self, shuffle):
        """Set shuffle mode."""
        if self._shuffle_dp:
            await self._shuffle_dp.async_set_value(self._device, shuffle)
        else:
            raise NotImplementedError()

    async def async_set_repeat(self, repeat):
        """Set repeat mode [all|one|off]."""
        if self._repeat_dp:
            await self._repeat_dp.async_set_value(self._device, repeat)
        else:
            raise NotImplementedError()
