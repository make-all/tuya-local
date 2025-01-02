"""
Setup for different kinds of Tuya water heater devices
"""

import logging

from homeassistant.components.water_heater import (
    ATTR_AWAY_MODE,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_OPERATION_MODE,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity, unit_from_ascii
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "water_heater",
        TuyaLocalWaterHeater,
    )


def validate_temp_unit(unit):
    translated_unit = unit_from_ascii(unit)
    try:
        return UnitOfTemperature(translated_unit)
    except ValueError:
        _LOGGER.warning("%s is not a valid temperature unit", unit)


class TuyaLocalWaterHeater(TuyaLocalEntity, WaterHeaterEntity):
    """Representation of a Tuya water heater entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the water heater device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)

        self._current_temperature_dps = dps_map.pop(
            ATTR_CURRENT_TEMPERATURE,
            None,
        )
        self._temperature_dps = dps_map.pop(ATTR_TEMPERATURE, None)
        self._unit_dps = dps_map.pop("temperature_unit", None)
        self._mintemp_dps = dps_map.pop("min_temperature", None)
        self._maxtemp_dps = dps_map.pop("max_temperature", None)
        self._operation_mode_dps = dps_map.pop(ATTR_OPERATION_MODE, None)
        self._away_mode_dps = dps_map.pop(ATTR_AWAY_MODE, None)
        self._init_end(dps_map)
        self._support_flags = WaterHeaterEntityFeature(0)

        if self._operation_mode_dps:
            self._support_flags |= WaterHeaterEntityFeature.OPERATION_MODE
            if self._operation_mode_dps.type is bool:
                self._support_flags |= WaterHeaterEntityFeature.ON_OFF
            if "away" in self._operation_mode_dps.values(device):
                self._support_flags |= WaterHeaterEntityFeature.AWAY_MODE
        if self._temperature_dps and not self._temperature_dps.readonly:
            self._support_flags |= WaterHeaterEntityFeature.TARGET_TEMPERATURE
        if self._away_mode_dps:
            self._support_flags |= WaterHeaterEntityFeature.AWAY_MODE

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # If there is a separate DPS that returns the units, use that
        if self._unit_dps:
            unit = validate_temp_unit(self._unit_dps.get_value(self._device))
            # Only return valid units
            if unit:
                return unit
        # If there unit attribute configured in the temperature dps, use that
        if self._temperature_dps and self._temperature_dps.unit:
            unit = validate_temp_unit(self._temperature_dps.unit)
            if unit:
                return unit
        if self._current_temperature_dps and self._current_temperature_dps.unit:
            unit = validate_temp_unit(self._current_temperature_dps.unit)
            if unit:
                return unit
        # Return the default unit
        return UnitOfTemperature.CELSIUS

    @property
    def precision(self):
        """Return the precision of the temperature setting."""
        # unlike sensor, this is a decimal of the smallest unit that can be
        # represented, not a number of decimal places.
        if self._temperature_dps is None:
            return None

        return 1.0 / max(
            self._temperature_dps.scale(self._device),
            (
                self._current_temperature_dps.scale(self._device)
                if self._current_temperature_dps
                else 1.0
            ),
        )

    @property
    def current_operation(self):
        """Return current operation ie. eco, electric, performance, ..."""
        return self._operation_mode_dps.get_value(self._device)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        if self._operation_mode_dps is None:
            return []
        else:
            return self._operation_mode_dps.values(self._device)

    @property
    def is_away_mode_on(self):
        if self._away_mode_dps:
            return self._away_mode_dps.get_value(self._device)
        elif self._operation_mode_dps and (
            "away" in self._operation_mode_dps.values(self._device)
        ):
            return self.current_operation == "away"

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._current_temperature_dps:
            return self._current_temperature_dps.get_value(self._device)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._temperature_dps is None:
            return None
        return self._temperature_dps.get_value(self._device)

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        dps = self._temperature_dps
        if dps is None:
            return 1
        return dps.step(self._device)

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature of the water heater."""
        if kwargs.get(ATTR_OPERATION_MODE) is not None:
            if self._operation_mode_dps is None:
                raise NotImplementedError()
            await self.async_set_operation_mode(
                kwargs.get(ATTR_OPERATION_MODE),
            )

        if kwargs.get(ATTR_TEMPERATURE) is not None:
            if self._temperature_dps is None:
                raise NotImplementedError()
            await self._temperature_dps.async_set_value(
                self._device, kwargs.get(ATTR_TEMPERATURE)
            )

    async def async_set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        if self._operation_mode_dps is None:
            raise NotImplementedError()
        await self._operation_mode_dps.async_set_value(
            self._device,
            operation_mode,
        )

    async def async_turn_away_mode_on(self):
        """Turn away mode on"""
        if self._away_mode_dps:
            await self._away_mode_dps.async_set_value(self._device, True)
        elif self._operation_mode_dps and (
            "away" in self._operation_mode_dps.values(self._device)
        ):
            await self.async_set_operation_mode("away")
        else:
            raise NotImplementedError()

    async def async_turn_away_mode_off(self):
        """Turn away mode off"""
        if self._away_mode_dps:
            await self._away_mode_dps.async_set_value(self._device, False)
        elif self._operation_mode_dps and (
            "away" in self._operation_mode_dps.values(self._device)
        ):
            # switch to the default mode
            await self.async_set_operation_mode(
                self._operation_mode_dps.default,
            )
        else:
            raise NotImplementedError()

    @property
    def min_temp(self):
        """Return the minimum supported target temperature."""
        # if a separate min_temperature dps is specified, the device tells us.
        if self._mintemp_dps is not None:
            return self._mintemp_dps.get_value(self._device)

        if self._temperature_dps:
            r = self._temperature_dps.range(self._device)
            return r[0]

    @property
    def max_temp(self):
        """Return the maximum supported target temperature."""
        # if a separate max_temperature dps is specified, the device tells us.
        if self._maxtemp_dps is not None:
            return self._maxtemp_dps.get_value(self._device)

        if self._temperature_dps:
            r = self._temperature_dps.range(self._device)
            return r[1]

    async def async_turn_on(self):
        """
        Turn on the water heater.  Works only if operation_mode is a
        boolean dp.
        """
        if self._operation_mode_dps and self._operation_mode_dps.type is bool:
            await self._device.async_set_property(
                self._operation_mode_dps.id,
                True,
            )

    async def async_turn_off(self):
        """
        Turn off the water heater.  Works only if operation_mode is a
        boolean dp.
        """
        if self._operation_mode_dps and self._operation_mode_dps.type is bool:
            await self._device.async_set_property(
                self._operation_mode_dps.id,
                False,
            )
