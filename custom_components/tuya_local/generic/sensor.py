"""
Platform to read Tuya sensors.
"""
from homeassistant.components.sensor import DEVICE_CLASSES, SensorEntity, STATE_CLASSES
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity


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
        self._sensor_dps = dps_map.pop("sensor")
        if self._sensor_dps is None:
            raise AttributeError(f"{config.name} is missing a sensor dps")
        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class of this device"""
        dclass = self._config.device_class
        if dclass in DEVICE_CLASSES:
            return dclass
        else:
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
        unit = self._sensor_dps.unit
        # Temperatures use Unicode characters, translate from simpler ASCII
        if unit == "C":
            unit = TEMP_CELSIUS
        elif unit == "F":
            unit = TEMP_FAHRENHEIT

        return unit
