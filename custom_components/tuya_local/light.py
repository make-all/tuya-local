"""
Setup for different kinds of Tuya light devices
"""

import logging
from struct import pack, unpack

import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_WHITE,
    EFFECT_OFF,
    ColorMode,
    LightEntity,
    LightEntityFeature,
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
        "light",
        TuyaLocalLight,
    )


class TuyaLocalLight(TuyaLocalEntity, LightEntity):
    """Representation of a Tuya WiFi-connected light."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the light.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The configuration for this entity.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._switch_dps = dps_map.pop("switch", None)
        self._brightness_dps = dps_map.pop("brightness", None)
        self._color_mode_dps = dps_map.pop("color_mode", None)
        self._color_temp_dps = dps_map.pop("color_temp", None)
        self._rgbhsv_dps = dps_map.pop("rgbhsv", None)
        self._named_color_dps = dps_map.pop("named_color", None)
        self._effect_dps = dps_map.pop("effect", None)
        self._init_end(dps_map)

        # Set min and max color temp
        if self._color_temp_dps:
            m = self._color_temp_dps._find_map_for_dps(0, self._device)
            if m:
                tr = m.get("target_range")
                if tr:
                    self._attr_min_color_temp_kelvin = tr.get("min")
                    self._attr_max_color_temp_kelvin = tr.get("max")

    @property
    def supported_color_modes(self):
        """Return the supported color modes for this light."""
        if self._color_mode_dps:
            return {
                ColorMode(mode)
                for mode in self._color_mode_dps.values(self._device)
                if mode and hasattr(ColorMode, mode.upper())
            }
        else:
            try:
                mode = ColorMode(self.color_mode)
                if mode and mode != ColorMode.UNKNOWN:
                    return {mode}
            except ValueError:
                _LOGGER.warning(
                    "%s/%s: Unrecognised color mode %s ignored",
                    self._config._device.config,
                    self.name or "light",
                    self.color_mode,
                )
        return set()

    @property
    def supported_features(self):
        """Return the supported features for this light."""
        if self.effect_list:
            return LightEntityFeature.EFFECT
        else:
            return LightEntityFeature(0)

    @property
    def color_mode(self):
        """Return the color mode of the light"""
        from_dp = self.raw_color_mode
        if from_dp:
            return from_dp

        if self._rgbhsv_dps:
            return ColorMode.HS
        elif self._named_color_dps:
            return ColorMode.HS
        elif self._color_temp_dps:
            return ColorMode.COLOR_TEMP
        elif self._brightness_dps:
            return ColorMode.BRIGHTNESS
        elif self._switch_dps:
            return ColorMode.ONOFF
        else:
            return ColorMode.UNKNOWN

    @property
    def raw_color_mode(self):
        """Return the color_mode as set from the dps."""
        if self._color_mode_dps:
            mode = self._color_mode_dps.get_value(self._device)
            if mode and hasattr(ColorMode, mode.upper()):
                return ColorMode(mode)

    @property
    def color_temp_kelvin(self):
        """Return the color temperature in kelvin."""
        if self._color_temp_dps and self.color_mode != ColorMode.HS:
            return self._color_temp_dps.get_value(self._device)

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

    def _brightness_control_by_hsv(self, target_mode=None):
        """Return whether brightness is controlled by HSV."""
        v_available = self._rgbhsv_dps and "v" in self._rgbhsv_dps.format["names"]
        b_available = self._brightness_dps is not None
        current_raw_mode = target_mode or self.raw_color_mode
        current_mode = target_mode or self.color_mode

        if current_raw_mode == ColorMode.HS and v_available:
            return True
        if current_raw_mode is None and current_mode == ColorMode.HS and v_available:
            return True
        if b_available:
            return False
        return v_available

    @property
    def brightness(self):
        """Get the current brightness of the light"""
        if self._brightness_control_by_hsv():
            return self._hsv_brightness
        return self._white_brightness

    @property
    def _white_brightness(self):
        if self._brightness_dps:
            r = self._brightness_dps.range(self._device)
            val = self._brightness_dps.get_value(self._device)
            if r and val:
                val = color_util.value_to_brightness(r, val)
            return val

    @property
    def _unpacked_rgbhsv(self):
        """Get the unpacked rgbhsv data"""
        if self._rgbhsv_dps:
            color = self._rgbhsv_dps.decoded_value(self._device)
            fmt = self._rgbhsv_dps.format
            if fmt and color:
                vals = unpack(fmt.get("format"), color)
                idx = 0
                rgbhsv = {}
                for v in vals:
                    # HA range: s = 0-100, rgbv = 0-255, h = 0-360
                    n = fmt["names"][idx]
                    r = fmt["ranges"][idx]
                    mx = r["max"]
                    scale = 1
                    if n == "h":
                        scale = 360 / mx
                    elif n == "s":
                        scale = 100 / mx
                    elif n in ["v", "r", "g", "b"]:
                        scale = 255 / mx

                    rgbhsv[n] = round(scale * v)
                    idx += 1

                return rgbhsv
        elif self._named_color_dps:
            colour = self._named_color_dps.get_value(self._device)
            if colour:
                rgb = color_util.color_name_to_rgb(colour)
                return {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

    @property
    def _hsv_brightness(self):
        """Get the colour mode brightness from the light"""
        rgbhsv = self._unpacked_rgbhsv
        if rgbhsv:
            return rgbhsv.get("v", self._white_brightness)
        return self._white_brightness

    @property
    def hs_color(self):
        """Get the current hs color of the light"""
        rgbhsv = self._unpacked_rgbhsv
        if rgbhsv:
            if "h" in rgbhsv and "s" in rgbhsv:
                hs = (rgbhsv["h"], rgbhsv["s"])
            else:
                r = rgbhsv.get("r")
                g = rgbhsv.get("g")
                b = rgbhsv.get("b")
                hs = color_util.color_RGB_to_hs(r, g, b)
            return hs

    @property
    def effect_list(self):
        """Return the list of valid effects for the light"""
        if self._effect_dps:
            return self._effect_dps.values(self._device)
        elif self._color_mode_dps:
            effects = [
                effect
                for effect in self._color_mode_dps.values(self._device)
                if effect and not hasattr(ColorMode, effect.upper())
            ]
            effects.append(EFFECT_OFF)
            return effects

    @property
    def effect(self):
        """Return the current effect setting of this light"""
        if self._effect_dps:
            return self._effect_dps.get_value(self._device)
        elif self._color_mode_dps:
            mode = self._color_mode_dps.get_value(self._device)
            if mode and not hasattr(ColorMode, mode.upper()):
                return mode
            return EFFECT_OFF

    def named_color_from_hsv(self, hs, brightness):
        """Get the named color from the rgb value"""
        if self._named_color_dps:
            palette = self._named_color_dps.values(self._device)
            xy = color_util.color_hs_to_xy(*hs)
            distance = float("inf")
            best_match = None
            for entry in palette:
                rgb = color_util.color_name_to_rgb(entry)
                xy_entry = color_util.color_RGB_to_xy(*rgb)
                d = color_util.get_distance_between_two_points(
                    color_util.XYPoint(*xy),
                    color_util.XYPoint(*xy_entry),
                )
                if d < distance:
                    distance = d
                    best_match = entry
            return best_match

    async def async_turn_on(self, **params):
        settings = {}
        color_mode = None
        _LOGGER.debug("Light turn_on: %s", params)
        if self._color_mode_dps and ATTR_WHITE in params:
            if self.color_mode != ColorMode.WHITE:
                color_mode = ColorMode.WHITE
            if ATTR_BRIGHTNESS not in params and self._brightness_dps:
                bright = params.get(ATTR_WHITE)
                _LOGGER.debug(
                    "Setting brightness via WHITE parameter to %d",
                    bright,
                )
                r = self._brightness_dps.range(self._device)
                if r:
                    bright = color_util.brightness_to_value(r, bright)

                settings = {
                    **settings,
                    **self._brightness_dps.get_values_to_set(
                        self._device,
                        bright,
                    ),
                }
        elif self._color_temp_dps and ATTR_COLOR_TEMP_KELVIN in params:
            if self.color_mode != ColorMode.COLOR_TEMP:
                color_mode = ColorMode.COLOR_TEMP

            color_temp = params.get(ATTR_COLOR_TEMP_KELVIN)
            # Light groups use the widest range from the lights in the
            # group, so we are expected to silently handle out of range values
            if color_temp < self.min_color_temp_kelvin:
                color_temp = self.min_color_temp_kelvin
            if color_temp > self.max_color_temp_kelvin:
                color_temp = self.max_color_temp_kelvin

            _LOGGER.debug("Setting color temp to %d", color_temp)
            settings = {
                **settings,
                **self._color_temp_dps.get_values_to_set(
                    self._device,
                    color_temp,
                ),
            }
        elif self._rgbhsv_dps and (
            ATTR_HS_COLOR in params
            or (ATTR_BRIGHTNESS in params and self._brightness_control_by_hsv())
        ):
            if self.color_mode != ColorMode.HS:
                color_mode = ColorMode.HS

            hs = params.get(ATTR_HS_COLOR, self.hs_color or (0, 0))
            brightness = params.get(ATTR_BRIGHTNESS, self.brightness or 255)
            fmt = self._rgbhsv_dps.format
            if hs and fmt:
                rgb = color_util.color_hsv_to_RGB(*hs, brightness / 2.55)
                rgbhsv = {
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[2],
                    "h": hs[0],
                    "s": hs[1],
                    "v": brightness,
                }
                _LOGGER.debug(
                    "Setting color as R:%d,G:%d,B:%d,H:%d,S:%d,V:%d",
                    rgb[0],
                    rgb[1],
                    rgb[2],
                    hs[0],
                    hs[1],
                    brightness,
                )

                current = self._unpacked_rgbhsv
                ordered = []
                idx = 0
                for n in fmt["names"]:
                    if n in rgbhsv:
                        r = fmt["ranges"][idx]
                        scale = 1
                        if n == "s":
                            scale = r["max"] / 100
                        elif n == "h":
                            scale = r["max"] / 360
                        else:
                            scale = r["max"] / 255
                        val = round(rgbhsv[n] * scale)
                        if val < r["min"]:
                            _LOGGER.warning(
                                "%s/%s: Color data %s=%d constrained to be above %d",
                                self._config._device.config,
                                self.name or "light",
                                n,
                                val,
                                r["min"],
                            )
                            val = r["min"]
                    else:
                        val = current[n]
                    ordered.append(val)
                    idx += 1
                binary = pack(fmt["format"], *ordered)
                settings = {
                    **settings,
                    **self._rgbhsv_dps.get_values_to_set(
                        self._device,
                        self._rgbhsv_dps.encode_value(binary),
                    ),
                }
        elif self._named_color_dps and ATTR_HS_COLOR in params:
            if self.color_mode != ColorMode.HS:
                color_mode = ColorMode.HS
            hs = params.get(ATTR_HS_COLOR, self.hs_color or (0, 0))
            brightness = params.get(ATTR_BRIGHTNESS, self.brightness or 255)
            best_match = self.named_color_from_hsv(hs, brightness)
            _LOGGER.debug("Setting color to %s", best_match)
            if best_match:
                settings = {
                    **settings,
                    **self._named_color_dps.get_values_to_set(
                        self._device,
                        best_match,
                    ),
                }
        if self._color_mode_dps:
            if color_mode:
                _LOGGER.debug("Auto setting color mode to %s", color_mode)
                settings = {
                    **settings,
                    **self._color_mode_dps.get_values_to_set(
                        self._device,
                        color_mode,
                    ),
                }
            elif not self._effect_dps:
                effect = params.get(ATTR_EFFECT)
                if effect:
                    if effect == EFFECT_OFF:
                        # Turn off the effect. Ideally this should keep the
                        # previous mode, but since the mode is shared with
                        # effect, use the default, or first in the list
                        effect = (
                            self._color_mode_dps.default
                            or self._color_mode_dps.values(self._device)[0]
                        )
                    _LOGGER.debug(
                        "Emulating effect using color mode of %s",
                        effect,
                    )
                    settings = {
                        **settings,
                        **self._color_mode_dps.get_values_to_set(
                            self._device,
                            effect,
                        ),
                    }

        if (
            ATTR_BRIGHTNESS in params
            and not self._brightness_control_by_hsv(color_mode)
            and self._brightness_dps
        ):
            bright = params.get(ATTR_BRIGHTNESS)
            _LOGGER.debug("Setting brightness to %s", bright)

            r = self._brightness_dps.range(self._device)
            if r:
                bright = color_util.brightness_to_value(r, bright)

            settings = {
                **settings,
                **self._brightness_dps.get_values_to_set(
                    self._device,
                    bright,
                ),
            }

        if self._effect_dps:
            effect = params.get(ATTR_EFFECT, None)
            if effect:
                _LOGGER.debug("Setting effect to %s", effect)
                settings = {
                    **settings,
                    **self._effect_dps.get_values_to_set(
                        self._device,
                        effect,
                    ),
                }

        if self._switch_dps and not self.is_on:
            if (
                self._switch_dps.readonly
                and self._effect_dps
                and "on" in self._effect_dps.values(self._device)
            ):
                # Special case for motion sensor lights with readonly switch
                # that have tristate switch available as effect
                if self._effect_dps.id not in settings:
                    settings = settings | self._effect_dps.get_values_to_set(
                        self._device, "on"
                    )
            else:
                settings = settings | self._switch_dps.get_values_to_set(
                    self._device, True
                )
        elif self._brightness_dps and not self.is_on:
            bright = 255
            r = self._brightness_dps.range(self._device)
            if r:
                bright = color_util.brightness_to_value(r, bright)

            settings = settings | self._brightness_dps.get_values_to_set(
                self._device, bright
            )

        if settings:
            await self._device.async_set_properties(settings)

    async def async_turn_off(self):
        if self._switch_dps:
            if (
                self._switch_dps.readonly
                and self._effect_dps
                and "off" in self._effect_dps.values(self._device)
            ):
                # Special case for motion sensor lights with readonly switch
                # that have tristate switch available as effect
                await self._effect_dps.async_set_value(self._device, "off")
            else:
                await self._switch_dps.async_set_value(self._device, False)
        elif self._brightness_dps:
            await self._brightness_dps.async_set_value(self._device, 0)
        else:
            raise NotImplementedError()

    async def async_toggle(self):
        disp_on = self.is_on

        await (self.async_turn_on() if not disp_on else self.async_turn_off())
