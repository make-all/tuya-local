"""
Platform for Tuya Number options that don't fit into other entity types.
"""
from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import (
    DEFAULT_MIN_VALUE,
    DEFAULT_MAX_VALUE,
)

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity, unit_from_ascii

MODE_AUTO = "auto"


class TuyaLocalNumber(TuyaLocalEntity, NumberEntity):
    """Representation of a Tuya Number"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        dps_map = self._init_begin(device, config)
        self._value_dps = dps_map.pop("value")
        if self._value_dps is None:
            raise AttributeError(f"{config.name} is missing a value dps")
        self._unit_dps = dps_map.pop("unit", None)
        self._min_dps = dps_map.pop("minimum", None)
        self._max_dps = dps_map.pop("maximum", None)
        self._init_end(dps_map)

    @property
    def native_min_value(self):
        if self._min_dps is not None:
            return self._min_dps.get_value(self._device)
        r = self._value_dps.range(self._device)
        return DEFAULT_MIN_VALUE if r is None else r["min"]

    @property
    def native_max_value(self):
        if self._max_dps is not None:
            return self._max_dps.get_value(self._device)
        r = self._value_dps.range(self._device)
        return DEFAULT_MAX_VALUE if r is None else r["max"]

    @property
    def native_step(self):
        return self._value_dps.step(self._device)

    @property
    def mode(self):
        """Return the mode."""
        m = self._config.mode
        if m is None:
            m = MODE_AUTO
        return m

    @property
    def native_unit_of_measurement(self):
        """Return the unit associated with this number."""
        if self._unit_dps is None:
            unit = self._value_dps.unit
        else:
            unit = self._unit_dps.get_value(self._device)

        return unit_from_ascii(unit)

    @property
    def native_value(self):
        """Return the current value of the number."""
        return self._value_dps.get_value(self._device)

    async def async_set_native_value(self, value):
        """Set the number."""
        await self._value_dps.async_set_value(self._device, value)
