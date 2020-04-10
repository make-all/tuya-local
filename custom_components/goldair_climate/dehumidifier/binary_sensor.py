"""
Platform to sense whether the dehumidifier tank is full.
"""

from homeassistant.components.binary_sensor import (BinarySensorDevice, DEVICE_CLASS_PROBLEM)
from custom_components.goldair_climate import GoldairTuyaDevice
from custom_components.goldair_climate.dehumidifier.climate import (
    ATTR_FAULT, FAULT_CODE_TO_DPS_CODE, PROPERTY_TO_DPS_ID
)

ATTR_FAULT_CODE = 'fault_code'
FAULT_TANK = 8
FAULT_NONE = 0

class GoldairDehumidifierTankFullBinarySensor(BinarySensorDevice):
    """Representation of a Goldair WiFi-connected dehumidifier Tank sensor."""

    def __init__(self, device):
        """Initialize the binary sensor.
        Args:
            device (GoldairTuyaDevice): The device API instance."""
        self._device = device
        self._fault = None

    @property
    def should_poll(self):
        """Return the polling state"""
        return True

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._device.name

    @property
    def is_on(self):
        """Return true if the tank is full."""
        if (self._fault is None):
            return None
        else:
            return self._fault == FAULT_TANK

    @property
    def device_class(self):
        """Return the class of device."""
        return DEVICE_CLASS_PROBLEM

    @property
    def device_state_attributes(self):
        """Return the state attributes"""
        attrs = {ATTR_FAULT_CODE: self._fault}
        # attrs.update(super().device_state_attributes)
        return attrs

    @property
    def available(self):
        """Return true if the device is available and value has not expired"""
        return self._fault is not None

    def update(self):
        self._device.refresh()
        self._fault = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_FAULT])

