"""
Setup for Tuya siren devices
"""

from homeassistant.components.siren import SirenEntity, SirenEntityFeature
from homeassistant.components.siren.const import (
    ATTR_DURATION,
    ATTR_TONE,
    ATTR_VOLUME_LEVEL,
)

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "siren",
        TuyaLocalSiren,
    )


class TuyaLocalSiren(TuyaLocalEntity, SirenEntity):
    """Representation of a Tuya siren"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the siren.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The config for this entity.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._tone_dp = dps_map.get(ATTR_TONE, None)
        self._volume_dp = dps_map.get(ATTR_VOLUME_LEVEL, None)
        self._duration_dp = dps_map.get(ATTR_DURATION, None)
        self._switch_dp = dps_map.get("switch", None)
        self._init_end(dps_map)
        # All control of features is through the turn_on service, so we need to
        # support that, even if the siren does not support direct control
        support = SirenEntityFeature(0)
        if self._tone_dp:
            support |= (
                SirenEntityFeature.TONES
                | SirenEntityFeature.TURN_ON
                | SirenEntityFeature.TURN_OFF
            )
            self._attr_available_tones = [
                x for x in self._tone_dp.values(device) if x != "off"
            ]
            self._default_tone = self._tone_dp.default

        if self._volume_dp:
            support |= SirenEntityFeature.VOLUME_SET
        if self._duration_dp:
            support |= SirenEntityFeature.DURATION
        if self._switch_dp:
            support |= SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF

        self._attr_supported_features = support

    @property
    def is_on(self):
        """Return whether the siren is on."""
        if self._switch_dp:
            return self._switch_dp.get_value(self._device)
        if self._tone_dp:
            return self._tone_dp.get_value(self._device) != "off"

    async def async_turn_on(self, **kwargs) -> None:
        tone = kwargs.get(ATTR_TONE, None)
        duration = kwargs.get(ATTR_DURATION, None)
        volume = kwargs.get(ATTR_VOLUME_LEVEL, None)

        set_dps = {}

        if self._tone_dp:
            if tone is None and not self._switch_dp:
                tone = self._tone_dp.get_value(self._device)
                if tone == "off":
                    tone = self._default_tone

            if tone is not None:
                set_dps = {
                    **set_dps,
                    **self._tone_dp.get_values_to_set(self._device, tone, set_dps),
                }

        if duration is not None and self._duration_dp:
            set_dps = {
                **set_dps,
                **self._duration_dp.get_values_to_set(self._device, duration, set_dps),
            }

        if volume is not None and self._volume_dp:
            # Volume is a float, range 0.0-1.0 in Home Assistant
            # In tuya it is likely an integer or a fixed list of values.
            # For integer, expect scale and step to do the conversion,
            # for fixed values, we need to snap to closest value.
            if self._volume_dp.values(self._device):
                volume = min(
                    self._volume_dp.values(self._device),
                    key=lambda x: abs(x - volume),
                )

            set_dps = {
                **set_dps,
                **self._volume_dp.get_values_to_set(self._device, volume, set_dps),
            }

        if self._switch_dp and not self.is_on:
            set_dps = {
                **set_dps,
                **self._switch_dp.get_values_to_set(self._device, True, set_dps),
            }

        await self._device.async_set_properties(set_dps)

    async def async_turn_off(self) -> None:
        """Turn off the siren"""
        if self._switch_dp:
            await self._switch_dp.async_set_value(self._device, False)
        elif self._tone_dp:
            await self._tone_dp.async_set_value(self._device, "off")
