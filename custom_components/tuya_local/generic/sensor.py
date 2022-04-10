"""
Platform to read Tuya sensors.
"""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    STATE_CLASSES,
)
import logging

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity, unit_from_ascii

_LOGGER = logging.getLogger(__name__)


class TuyaLocalSensor(TuyaLocalEntity, SensorEntity):
    """Representation of a Tuya Sensor"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        dps_map = self._init_begin(device, config)
        self._sensor_dps = dps_map.pop("sensor", None)
        if self._sensor_dps is None:
            raise AttributeError(f"{config.name} is missing a sensor dps")
        self._unit_dps = dps_map.pop("unit", None)

        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class of this device"""
        dclass = self._config.device_class
        try:
            return SensorDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(f"Unrecognized sensor device class of {dclass} ignored")
            return None

    @property
    def state_class(self):
        """Return the state class of this entity"""
        sclass = self._sensor_dps.state_class
        if sclass in STATE_CLASSES:
            return sclass
        else:
            return None

    @property
    def native_value(self):
        """Return the value reported by the sensor"""
        return self._sensor_dps.get_value(self._device)

    @property
    def native_unit_of_measurement(self):
        """Return the unit for the sensor"""
        if self._unit_dps is None:
            unit = self._sensor_dps.unit
        else:
            unit = self._unit_dps.get_value(self._device)

        return unit_from_ascii(unit)
