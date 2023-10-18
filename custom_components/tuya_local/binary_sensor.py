"""
Setup for different kinds of Tuya Binary sensors
"""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "binary_sensor",
        TuyaLocalBinarySensor,
    )


class TuyaLocalBinarySensor(TuyaLocalEntity, BinarySensorEntity):
    """Representation of a Tuya Binary Sensor"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._sensor_dps = dps_map.pop("sensor")
        if self._sensor_dps is None:
            raise AttributeError(f"{config.config_id} is missing a sensor dps")
        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class of this device"""
        dclass = self._config.device_class
        try:
            return BinarySensorDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(
                    "%s/%s: Unrecognised binary_sensor device class of %s ignored",
                    self._config._device.config,
                    self.name or "binary_sensor",
                    dclass,
                )
            return None

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._sensor_dps.get_value(self._device)
