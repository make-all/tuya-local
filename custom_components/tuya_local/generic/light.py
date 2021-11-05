"""
Platform to control Tuya lights.
Initially based on the secondary panel lighting control on some climate
devices, so only providing simple on/off control.
"""
from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
    COLOR_MODE_UNKNOWN,
    SUPPORT_EFFECT,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity


class TuyaLocalLight(TuyaLocalEntity, LightEntity):
    """Representation of a Tuya WiFi-connected light."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the light.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The configuration for this entity.
        """
        dps_map = self._init_begin(device, config)
        self._switch_dps = dps_map.pop("switch", None)
        self._brightness_dps = dps_map.pop("brightness", None)
        self._effect_dps = dps_map.pop("effect", None)
        self._init_end(dps_map)

    @property
    def supported_color_modes(self):
        """Return the supported color modes for this light."""
        if self._brightness_dps:
            return [COLOR_MODE_BRIGHTNESS]
        elif self._switch_dps:
            return [COLOR_MODE_ONOFF]
        else:
            return []

    @property
    def supported_features(self):
        """Return the supported features for this light."""
        if self._effect_dps:
            return SUPPORT_EFFECT
        else:
            return 0

    @property
    def color_mode(self):
        """Return the color mode of the light"""
        if self._brightness_dps:
            return COLOR_MODE_BRIGHTNESS
        elif self._switch_dps:
            return COLOR_MODE_ONOFF
        else:
            return COLOR_MODE_UNKNOWN

    @property
    def is_on(self):
        """Return the current state."""
        if self._switch_dps:
            return self._switch_dps.get_value(self._device)
        elif self._brightness_dps:
            b = self.brightness
            return isinstance(b, int) and b > 0
        else:
            # There shouldn't be lights without control, but if there are, assume always on if they are responding
            return self.available

    @property
    def brightness(self):
        """Get the current brightness of the light"""
        if self._brightness_dps is None:
            return None
        return self._brightness_dps.get_value(self._device)

    @property
    def effect_list(self):
        """Return the list of valid effects for the light"""
        if self._effect_dps is None:
            return None
        return self._effect_dps.values(self._device)

    @property
    def effect(self):
        """Return the current effect setting of this light"""
        if self._effect_dps is None:
            return None
        return self._effect_dps.get_value(self._device)

    async def async_turn_on(self, **params):
        settings = {}
        if self._switch_dps:
            settings = {
                **settings,
                **self._switch_dps.get_values_to_set(self._device, True),
            }

        if self._brightness_dps:
            bright = params.get(ATTR_BRIGHTNESS, 255)
            bright_values = self._brightness_dps.get_values_to_set(self._device, bright)
            settings = {
                **settings,
                **bright_values,
            }
        if self._effect_dps:
            effect = params.get(ATTR_EFFECT, None)
            if effect:
                effect_values = self._effect_dps.get_values_to_set(self._device, effect)
                settings = {
                    **settings,
                    **effect_values,
                }

        await self._device.async_set_properties(settings)

    async def async_turn_off(self):
        if self._switch_dps:
            await self._switch_dps.async_set_value(self._device, False)
        elif self._brightness_dps:
            await self._brightness_dps.async_set_value(self._device, 0)
        else:
            raise NotImplementedError()

    async def async_toggle(self):
        dps_display_on = self.is_on

        await (self.async_turn_on() if not dps_display_on else self.async_turn_off())
