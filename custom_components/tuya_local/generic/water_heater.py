"""
Platform to control tuya water heater devices.
"""
import logging

from homeassistant.components.water_heater import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_OPERATION_MODE,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity, unit_from_ascii

_LOGGER = logging.getLogger(__name__)


def validate_temp_unit(unit):
    unit = unit_from_ascii(unit)
    try:
        return UnitOfTemperature(unit)
    except ValueError:
        return None


class TuyaLocalWaterHeater(TuyaLocalEntity, WaterHeaterEntity):
    """Representation of a Tuya water heater entity."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the water heater device.
        Args:
           device (TuyaLocalDevice): The device API instance.
           config (TuyaEntityConfig): The entity config.
        """
        dps_map = self._init_begin(device, config)

        self._current_temperature_dps = dps_map.pop(ATTR_CURRENT_TEMPERATURE, None)
        self._temperature_dps = dps_map.pop(ATTR_TEMPERATURE, None)
        self._unit_dps = dps_map.pop("temperature_unit", None)
        self._mintemp_dps = dps_map.pop("min_temperature", None)
        self._maxtemp_dps = dps_map.pop("max_temperature", None)
        self._operation_mode_dps = dps_map.pop("operation_mode", None)
        self._init_end(dps_map)
        self._support_flags = 0

        if self._operation_mode_dps:
            self._support_flags |= WaterHeaterEntityFeature.OPERATION_MODE
        if self._temperature_dps and not self._temperature_dps.readonly:
            self._support_flags |= WaterHeaterEntityFeature.TARGET_TEMPERATURE

    @property
    def supported_features(self):
        """Return the features supported by this climate device."""
        return self._support_flags

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # If there is a separate DPS that returns the units, use that
        if self._unit_dps is not None:
            unit = validate_temp_unit(self._unit_dps.get_value(self._device))
            # Only return valid units
            if unit is not None:
                return unit
        # If there unit attribute configured in the temperature dps, use that
        if self._temperature_dps:
            unit = validate_temp_unit(self._temperature_dps.unit)
            if unit is not None:
                return unit
        # Return the default unit from the device
        return UnitOfTemperature.CELSIUS

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
    def current_temperature(self):
        """Return the current temperature."""
        if self._current_temperature_dps is None:
            return None
        return self._current_temperature_dps.get_value(self._device)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._temperature_dps is None:
            raise NotImplementedError()
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
            await self.async_set_operation_mode(kwargs.get(ATTR_OPERATION_MODE))

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
        await self._operation_mode_dps.async_set_value(self._device, operation_mode)

    @property
    def min_temp(self):
        """Return the minimum supported target temperature."""
        # if a separate min_temperature dps is specified, the device tells us.
        if self._mintemp_dps is not None:
            return self._mintemp_dps.get_value(self._device)

        if self._temperature_dps:
            r = self._temperature_dps.range(self._device)
            return r.get("min")

    @property
    def max_temp(self):
        """Return the maximum supported target temperature."""
        # if a separate max_temperature dps is specified, the device tells us.
        if self._maxtemp_dps is not None:
            return self._maxtemp_dps.get_value(self._device)

        if self._temperature_dps:
            r = self._temperature_dps.range(self._device)
            return r.get("max")
