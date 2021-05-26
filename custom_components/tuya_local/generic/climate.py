"""
Platform to control tuya climate devices.
"""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_PRESET_MODE,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    HVAC_MODE_HEAT,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


class TuyaLocalClimate(ClimateEntity):
    """Representation of a Tuya Climate entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the climate device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        self._device = device
        self._config = config
        self._support_flags = 0
        self._current_temperature_dps = None
        self._temperature_dps = None
        self._preset_mode_dps = None
        self._hvac_mode_dps = None
        self._attr_dps = []
        self._temperature_step = 1

        for d in config.dps():
            if d.name == "hvac_mode":
                self._hvac_mode_dps = d
            elif d.name == "temperature":
                self._temperature_dps = d
                self._support_flags |= SUPPORT_TARGET_TEMPERATURE

            elif d.name == "current_temperature":
                self._current_temperature_dps = d
            elif d.name == "preset_mode":
                self._preset_mode_dps = d
                self._support_flags |= SUPPORT_PRESET_MODE
            else:
                self._attr_dps.append(d)

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._device.name

    @property
    def friendly_name(self):
        """Return the friendly name of the climate entity for the UI."""
        return self._config.name

    @property
    def unique_id(self):
        """Return the unique id for this climate device."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this heater."""
        return self._device.device_info

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.hvac_mode == HVAC_MODE_HEAT:
            return "mdi:radiator"
        else:
            return "mdi:radiator-disabled"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the currently set target temperature."""
        if self._temperature_dps is None:
            raise NotImplementedError()
        return self._temperature_dps.get_value(self._device)

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._temperature_step

    @property
    def min_temp(self):
        """Return the minimum supported target temperature."""
        if self._temperature_dps is None or self._temperature_dps.range is None:
            return DEFAULT_MIN_TEMP
        return self._temperature_dps.range["min"]

    @property
    def max_temp(self):
        """Return the maximum supported target temperature."""
        if self._temperature_dps is None or self._temperature_dps.range is None:
            return DEFAULT_MIN_TEMP
        return self._temperature_dps.range["max"]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_PRESET_MODE) is not None:
            await self.async_set_preset_mode(kwargs.get(ATTR_PRESET_MODE))
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    async def async_set_target_temperature(self, target_temperature):
        if self._temperature_dps is None:
            raise NotImplementedError()

        target_temperature = int(round(target_temperature))
        if not self.min_temp <= target_temperature <= self.max_temp:
            raise ValueError(
                f"Target temperature ({target_temperature}) must be between "
                f"{self.min_temp} and {self.max_temp}."
            )

        await self._temperature_dps.async_set_value(self._device, target_temperature)

    @property
    def current_temperature(self):
        """Return this current temperature."""
        if self._current_temperature_dps is None:
            return None
        return self._current_temperature_dps.get_value(self._device)

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        if self._hvac_mode_dps is None:
            raise NotImplementedError()
        hvac_mode = self._hvac_mode_dps.get_value(self._device)
        return STATE_UNAVAILABLE if hvac_mode is None else hvac_mode

    @property
    def hvac_modes(self):
        """Return available HVAC modes."""
        if self._hvac_mode_dps is None:
            return None
        else:
            return self._hvac_mode_dps.values

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        if self._hvac_mode_dps is None:
            raise NotImplementedError()
        await self._hvac_mode_dps.async_set_value(self._device, hvac_mode)

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self._preset_mode_dps is None:
            raise NotImplementedError()
        return self._preset_mode_dps.get_value(self._device)

    @property
    def preset_modes(self):
        """Return the list of presets that this device supports."""
        if self._preset_mode_dps is None:
            return None
        return self._preset_mode_dps.values

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""
        if self._preset_mode_dps is None:
            raise NotImplementedError()
        await self._preset_mode_dps.async_set_value(self._device, preset_mode)

    @property
    def device_state_attributes(self):
        """Get additional attributes that the integration itself does not support."""
        attr = {}
        for a in self._attr_dps:
            attr[a.name] = a.get_value(self._device)
        return attr

    async def async_update(self):
        await self._device.async_refresh()
