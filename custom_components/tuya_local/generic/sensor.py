"""
Platform to read Tuya sensors.
"""
from homeassistant.components.sensor import DEVICE_CLASSES, SensorEntity, STATE_CLASSES
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig


class TuyaLocalSensor(SensorEntity):
    """Representation of a Tuya Sensor"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        self._device = device
        self._config = config
        self._attr_dps = []
        dps_map = {c.name: c for c in config.dps()}
        self._sensor_dps = dps_map.pop("sensor")

        if self._sensor_dps is None:
            raise AttributeError(f"{config.name} is missing a sensor dps")

        for d in dps_map.values():
            if not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name for this entity."""
        return self._config.name(self._device.name)

    @property
    def unique_id(self):
        """Return the unique id of the device."""
        return self._config.unique_id(self._device.unique_id)

    @property
    def device_info(self):
        """Return device information about the device."""
        return self._device.device_info

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

    async def async_update(self):
        await self._device.async_refresh()
