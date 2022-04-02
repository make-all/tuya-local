"""
Platform to control Tuya lights.
Initially based on the secondary panel lighting control on some climate
devices, so only providing simple on/off control.
"""
from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_RGBW_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_ONOFF,
    COLOR_MODE_RGBW,
    COLOR_MODE_UNKNOWN,
    SUPPORT_EFFECT,
    VALID_COLOR_MODES,
)
import homeassistant.util.color as color_util

import logging
from struct import pack, unpack

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


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
        self._color_temp_dps = dps_map.pop("color_temp", None)
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
        else:
            mode = self.color_mode
            if mode and mode != COLOR_MODE_UNKNOWN:
                return [mode]

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
        elif self._color_temp_dps:
            return COLOR_MODE_COLOR_TEMP
        elif self._brightness_dps:
            return COLOR_MODE_BRIGHTNESS
        elif self._switch_dps:
            return COLOR_MODE_ONOFF
        else:
            return COLOR_MODE_UNKNOWN

    @property
    def color_temp(self):
        """Return the color temperature in mireds"""
        if self._color_temp_dps:
            unscaled = self._color_temp_dps.get_value(self._device)
            range = self._color_temp_dps.range(self._device)
            if range:
                min = range["min"]
                max = range["max"]
                return round(unscaled * 347 / (max - min) + 153 - min)
            else:
                return unscaled
        return None

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
        if self._rgbhsv_dps:
            # color data in hex format RRGGBBHHHHSSVV (14 digit hex)
            # can also be base64 encoded.
            # Either RGB or HSV can be used.
            color = self._rgbhsv_dps.decoded_value(self._device)

            format = self._rgbhsv_dps.format
            if format:
                vals = unpack(format.get("format"), color)
                rgbhsv = {}
                idx = 0
                for v in vals:
                    # Range in HA is 0-100 for s, 0-255 for rgb and v, 0-360
                    # for h
                    n = format["names"][idx]
                    r = format["ranges"][idx]
                    if r["min"] != 0:
                        raise AttributeError(
                            f"Unhandled minimum range for {n} in RGBW value"
                        )
                    max = r["max"]
                    scale = 1
                    if n == "h":
                        scale = 360 / max
                    elif n == "s":
                        scale = 100 / max
                    else:
                        scale = 255 / max

                    rgbhsv[n] = round(scale * v)
                    idx += 1

                h = rgbhsv["h"]
                s = rgbhsv["s"]
                # convert RGB from H and S to seperate out the V component
                r, g, b = color_util.color_hs_to_RGB(h, s)
                w = rgbhsv["v"]
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
            if color_mode:
                color_values = self._color_mode_dps.get_values_to_set(
                    self._device, color_mode
                )
                settings = {
                    **settings,
                    **color_values,
                }
            elif not self._effect_dps:
                effect = params.get(ATTR_EFFECT)
                if effect:
                    color_values = self._color_mode_dps.get_values_to_set(
                        self._device, effect
                    )
                    settings = {
                        **settings,
                        **color_values,
                    }

        if self._color_temp_dps:
            color_temp = params.get(ATTR_COLOR_TEMP)
            range = self._color_temp_dps.range(self._device)

            if range and color_temp:
                min = range["min"]
                max = range["max"]
                color_temp = round((color_temp - 153 + min) * (max - min) / 347)

            if color_temp:
                color_values = self._color_temp_dps.get_values_to_set(
                    self._device,
                    color_temp,
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
            format = self._rgbhsv_dps.format
            if rgbw and format:
                rgb = (rgbw[0], rgbw[1], rgbw[2])
                hs = color_util.color_RGB_to_hs(rgbw[0], rgbw[1], rgbw[2])
                rgbhsv = {
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[3],
                    "h": hs[0],
                    "s": hs[1],
                    "v": rgbw[3],
                }
                ordered = []
                idx = 0
                for n in format["names"]:
                    r = format["ranges"][idx]
                    scale = 1
                    if n == "s":
                        scale = r["max"] / 100
                    elif n == "h":
                        scale = r["max"] / 360
                    else:
                        scale = r["max"] / 255
                    ordered[idx] = round(rgbhsv[n] * scale)
                    idx += 1

                binary = pack(format["format"], (*ordered,))
                color_dps = self._rgbhsv_dps.get_values_to_set(
                    self._device,
                    self._rgbhsv_dps.encode_value(binary),
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
        disp_on = self.is_on

        await (self.async_turn_on() if not disp_on else self.async_turn_off())
