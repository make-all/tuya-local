"""
Platform to control Tuya lights.
Initially based on the secondary panel lighting control on some climate
devices, so only providing simple on/off control.
"""
from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
    COLOR_MODE_UNKNOWN,
    SUPPORT_EFFECT,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig


class TuyaLocalLight(LightEntity):
    """Representation of a Tuya WiFi-connected light."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the light.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The configuration for this entity.
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        dps_map = {c.name: c for c in config.dps()}
        self._switch_dps = dps_map.pop("switch", None)
        self._brightness_dps = dps_map.pop("brightness", None)
        self._effect_dps = dps_map.pop("effect", None)

        for d in dps_map.values():
            if not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the light."""
        return self._device.name

    @property
    def friendly_name(self):
        """Return the friendly name for this entity."""
        return self._config.name

    @property
    def unique_id(self):
        """Return the unique id for this heater LED display."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this heater LED display."""
        return self._device.device_info

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        icon = self._config.icon(self._device)
        if icon:
            return icon
        else:
            return super().icon

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
            # There shouldn't be lights without control, but if there are, assume always on
            return True

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

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

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

    async def async_update(self):
        await self._device.async_refresh()
