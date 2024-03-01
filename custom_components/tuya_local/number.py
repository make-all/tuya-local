"""
Setup for different kinds of Tuya numbers
"""

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import (
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    NumberDeviceClass,
)

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity, unit_from_ascii

_LOGGER = logging.getLogger(__name__)

MODE_AUTO = "auto"


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "number",
        TuyaLocalNumber,
    )


class TuyaLocalNumber(TuyaLocalEntity, NumberEntity):
    """Representation of a Tuya Number"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._value_dps = dps_map.pop("value")
        if self._value_dps is None:
            raise AttributeError(f"{config.config_id} is missing a value dps")
        self._unit_dps = dps_map.pop("unit", None)
        self._min_dps = dps_map.pop("minimum", None)
        self._max_dps = dps_map.pop("maximum", None)
        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class of this device"""
        dclass = self._config.device_class
        if dclass:
            try:
                return NumberDeviceClass(dclass)
            except ValueError:
                _LOGGER.warning(
                    "%s/%s: Unrecognized number device class of %s ignored",
                    self._config._device.config,
                    self.name or "number",
                    dclass,
                )

    @property
    def native_min_value(self):
        if self._min_dps is not None:
            return self._min_dps.get_value(self._device)
        r = self._value_dps.range(self._device)
        return DEFAULT_MIN_VALUE if r is None else r[0]

    @property
    def native_max_value(self):
        if self._max_dps is not None:
            return self._max_dps.get_value(self._device)
        r = self._value_dps.range(self._device)
        return DEFAULT_MAX_VALUE if r is None else r[1]

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
