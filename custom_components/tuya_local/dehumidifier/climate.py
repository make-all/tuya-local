"""
Goldair WiFi Dehumidifier device.
"""
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, STATE_UNAVAILABLE
)
from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    ATTR_FAN_MODE, ATTR_HUMIDITY, ATTR_HVAC_MODE, ATTR_PRESET_MODE,
    FAN_OFF, FAN_LOW, FAN_HIGH,
    HVAC_MODE_OFF, HVAC_MODE_DRY,
    SUPPORT_TARGET_HUMIDITY, SUPPORT_PRESET_MODE, SUPPORT_FAN_MODE
)
from custom_components.tuya_local import TuyaLocalDevice

ATTR_TARGET_HUMIDITY = 'target_humidity'
ATTR_AIR_CLEAN_ON = 'air_clean_on'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_FAULT = 'fault'
ATTR_DISPLAY_ON = 'display_on'

PRESET_NORMAL = 'Normal'
PRESET_LOW = 'Low'
PRESET_HIGH = 'High'
PRESET_DRY_CLOTHES = 'Dry clothes'
PRESET_AIR_CLEAN = 'Air clean'

FAULT_NONE = 'No fault'
FAULT_TANK = 'Tank full or missing'

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: '1',
    ATTR_PRESET_MODE: '2',
    ATTR_TARGET_HUMIDITY: '4',
    ATTR_AIR_CLEAN_ON: '5',
    ATTR_FAN_MODE: '6',
    ATTR_CHILD_LOCK: '7',
    ATTR_FAULT: '11',
    ATTR_DISPLAY_ON: '102',
    ATTR_TEMPERATURE: '103',
    ATTR_HUMIDITY: '104'
}

HVAC_MODE_TO_DPS_MODE = {
    HVAC_MODE_OFF: False,
    HVAC_MODE_DRY: True
}
PRESET_MODE_TO_DPS_MODE = {
    PRESET_NORMAL: '0',
    PRESET_LOW: '1',
    PRESET_HIGH: '2',
    PRESET_DRY_CLOTHES: '3'
}
FAN_MODE_TO_DPS_MODE = {
    FAN_LOW: '1',
    FAN_HIGH: '3'
}
FAULT_CODE_TO_DPS_CODE = {
    FAULT_NONE: 0,
    FAULT_TANK: 8
}

SUPPORT_FLAGS = SUPPORT_TARGET_HUMIDITY | SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE


class GoldairDehumidifier(ClimateDevice):
    """Representation of a Goldair WiFi dehumidifier."""

    def __init__(self, device):
        """Initialize the dehumidifier.
        Args:
            name (str): The device's name.
            device (TuyaLocalDevice): The device API instance."""
        self._device = device

        self._support_flags = SUPPORT_FLAGS

        self._HUMIDITY_STEP = 5
        self._HUMIDITY_LIMITS = {
            'min': 30,
            'max': 80
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
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
    def current_humidity(self):
        """Return the current reading of the humidity sensor."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HUMIDITY])

    @property
    def min_humidity(self):
        """Return the minimum humidity setting."""
        return self._HUMIDITY_LIMITS['min']

    @property
    def max_humidity(self):
        """Return the maximum humidity setting."""
        return self._HUMIDITY_LIMITS['max']

    @property
    def target_humidity(self):
        """Return the current target humidity."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY])

    def set_humidity(self, humidity):
        """Set the device's target humidity."""
        if self.preset_mode in [PRESET_AIR_CLEAN, PRESET_DRY_CLOTHES]:
            raise ValueError('Humidity can only be changed while in Normal, Low or High preset modes.')
        humidity = int(self._HUMIDITY_STEP * round(float(humidity) / self._HUMIDITY_STEP))
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY], humidity)

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def min_temp(self):
        """Return the minimum temperature setting."""
        return None

    @property
    def max_temp(self):
        """Return the maximum temperature setting."""
        return None

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE])

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Dry or Off."""
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE])

        if dps_mode is not None:
            return TuyaLocalDevice.get_key_for_value(HVAC_MODE_TO_DPS_MODE, dps_mode)
        else:
            return STATE_UNAVAILABLE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return list(HVAC_MODE_TO_DPS_MODE.keys())

    def set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = HVAC_MODE_TO_DPS_MODE[hvac_mode]
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode)

    @property
    def preset_mode(self):
        """Return current preset mode, ie Normal, Low, High, Dry Clothes, or Air Clean."""
        air_clean_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON])
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE])

        if air_clean_on:
            return PRESET_AIR_CLEAN
        elif dps_mode is not None:
            return TuyaLocalDevice.get_key_for_value(PRESET_MODE_TO_DPS_MODE, dps_mode)
        else:
            return None

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return list(PRESET_MODE_TO_DPS_MODE.keys()) + [PRESET_AIR_CLEAN]

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        if preset_mode == PRESET_AIR_CLEAN:
            self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON], True)
            self._device.anticipate_property_value(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH)
        else:
            dps_mode = PRESET_MODE_TO_DPS_MODE[preset_mode]
            self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON], False)
            self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE], dps_mode)
            if preset_mode == PRESET_LOW:
                self._device.anticipate_property_value(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_LOW)
            elif preset_mode in [PRESET_HIGH, PRESET_DRY_CLOTHES]:
                self._device.anticipate_property_value(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH)

    @property
    def fan_mode(self):
        """Return the fan mode."""
        preset = self.preset_mode

        if preset in [PRESET_HIGH, PRESET_DRY_CLOTHES, PRESET_AIR_CLEAN]:
            return FAN_HIGH
        elif preset == PRESET_LOW:
            return FAN_LOW
        else:
            dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE])
            if dps_mode is not None:
                return TuyaLocalDevice.get_key_for_value(FAN_MODE_TO_DPS_MODE, dps_mode)
            else:
                return None

    @property
    def fan_modes(self):
        """List of fan modes."""
        preset = self.preset_mode

        if preset in [PRESET_HIGH, PRESET_DRY_CLOTHES, PRESET_AIR_CLEAN]:
            return [FAN_HIGH]
        elif preset == PRESET_LOW:
            return [FAN_LOW]
        elif preset == PRESET_NORMAL:
            return list(FAN_MODE_TO_DPS_MODE.keys())
        else:
            return []

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        if self.preset_mode != PRESET_NORMAL:
            raise ValueError('Fan mode can only be changed while in Normal preset mode.')

        if fan_mode not in FAN_MODE_TO_DPS_MODE.keys():
            raise ValueError(f'Invalid fan mode: {fan_mode}')

        dps_mode = FAN_MODE_TO_DPS_MODE[fan_mode]
        self._device.set_property(PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], dps_mode)

    @property
    def fault(self):
        """Get the current fault status."""
        fault = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_FAULT])
        if fault is None or fault == FAULT_NONE:
            return None
        else:
            return TuyaLocalDevice.get_key_for_value(FAULT_CODE_TO_DPS_CODE, fault)

    def update(self):
        self._device.refresh()
