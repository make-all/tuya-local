"""
Platform to control Tuya lights.
Initially based on the secondary panel lighting control on some climate
devices, so only providing simple on/off control.
"""
from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_EFFECT,
    ATTR_RGBW_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
    COLOR_MODE_RGBW,
    COLOR_MODE_UNKNOWN,
    SUPPORT_EFFECT,
    VALID_COLOR_MODES,
)
import homeassistant.util.color as color_util

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
        self._color_mode_dps = dps_map.pop("color_mode", None)
        self._rgbhsv_dps = dps_map.pop("rgbhsv", None)
        self._effect_dps = dps_map.pop("effect", None)
        self._init_end(dps_map)

    @property
    def supported_color_modes(self):
        """Return the supported color modes for this light."""
        if self._color_mode_dps:
            return [
                mode
                for mode in self._color_mode_dps.values(self._device)
                if mode in VALID_COLOR_MODES
            ]

        elif self._rgbhsv_dps:
            return [COLOR_MODE_RGBW]
        elif self._brightness_dps:
            return [COLOR_MODE_BRIGHTNESS]
        elif self._switch_dps:
            return [COLOR_MODE_ONOFF]
        else:
            return []

    @property
    def supported_features(self):
        """Return the supported features for this light."""
        if self.effect_list:
            return SUPPORT_EFFECT
        else:
            return 0

    @property
    def color_mode(self):
        """Return the color mode of the light"""
        if self._color_mode_dps:
            mode = self._color_mode_dps.get_value(self._device)
            if mode in VALID_COLOR_MODES:
                return mode

        if self._rgbhsv_dps:
            return COLOR_MODE_RGBW
        elif self._brightness_dps:
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
            # There shouldn't be lights without control, but if there are,
            # assume always on if they are responding
            return self.available

    @property
    def brightness(self):
        """Get the current brightness of the light"""
        if self._brightness_dps:
            return self._brightness_dps.get_value(self._device)

    @property
    def rgbw_color(self):
        """Get the current RGBW color of the light"""
        if self._rgbhsv_dps and self._rgbhsv_dps.rawtype == "hex":
            # color data in hex format RRGGBBHHHHSSVV (14 digit hex)
            # Either RGB or HSV can be used.
            color = self._rgbhsv_dps.get_value(self._device)
            h = int(color[6:10], 16)
            s = int(color[10:12], 16)
            r, g, b = color_util.color_hs_to_RGB(h, s)
            w = int(color[12:14], 16) * 255 / 100
            return (r, g, b, w)

    @property
    def effect_list(self):
        """Return the list of valid effects for the light"""
        if self._effect_dps:
            return self._effect_dps.values(self._device)
        elif self._color_mode_dps:
            return [
                effect
                for effect in self._color_mode_dps.values(self._device)
                if effect not in VALID_COLOR_MODES
            ]

    @property
    def effect(self):
        """Return the current effect setting of this light"""
        if self._effect_dps:
            return self._effect_dps.get_value(self._device)
        elif self._color_mode_dps:
            mode = self._color_mode_dps.get_value(self._device)
            if mode in VALID_COLOR_MODES:
                return None
            return mode

    async def async_turn_on(self, **params):
        settings = {}
        if self._switch_dps:
            settings = {
                **settings,
                **self._switch_dps.get_values_to_set(self._device, True),
            }

        if self._color_mode_dps:
            color_mode = params.get(ATTR_COLOR_MODE)
            effect = params.get(ATTR_EFFECT)
            if color_mode:
                color_values = self._color_mode_dps.get_values_to_set(
                    self._device, color_mode
                )
                settings = {
                    **settings,
                    **color_values,
                }

        if self._brightness_dps:
            bright = params.get(ATTR_BRIGHTNESS, 255)
            bright_values = self._brightness_dps.get_values_to_set(
                self._device,
                bright,
            )
            settings = {
                **settings,
                **bright_values,
            }

        if self._rgbhsv_dps:
            rgbw = params.get(ATTR_RGBW_COLOR, None)
            if rgbw:
                rgb = (rgbw[0], rgbw[1], rgbw[2])
                hs = color_util.color_RGB_to_hs(rgb)
                color = "{:02x}{:02x}{:02x}{:04x}{:02x}{:02x}".format(
                    round(rgb[0]),
                    round(rgb[1]),
                    round(rgb[2]),
                    round(hs[0]),
                    round(hs[1]),
                    round(rgbw[3] * 100 / 255),
                )
                color_dps = self._rgbhsv_dps.get_values_to_set(
                    self._device,
                    color,
                )
                settings = {**settings, **color_dps}

        if self._effect_dps:
            effect = params.get(ATTR_EFFECT, None)
            if effect:
                effect_values = self._effect_dps.get_values_to_set(
                    self._device,
                    effect,
                )
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
