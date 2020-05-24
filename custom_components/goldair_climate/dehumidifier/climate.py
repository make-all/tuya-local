"""
Goldair WiFi Dehumidifier device.
"""
try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity

from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    FAN_HIGH,
    FAN_LOW,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from ..device import GoldairTuyaDevice
from .const import (
    ATTR_AIR_CLEAN_ON,
    ATTR_DEFROSTING,
    ATTR_ERROR,
    ATTR_TARGET_HUMIDITY,
    ERROR_CODE_TO_DPS_CODE,
    ERROR_TANK,
    FAN_MODE_TO_DPS_MODE,
    HVAC_MODE_TO_DPS_MODE,
    PRESET_AIR_CLEAN,
    PRESET_DRY_CLOTHES,
    PRESET_HIGH,
    PRESET_LOW,
    PRESET_MODE_TO_DPS_MODE,
    PRESET_NORMAL,
    PROPERTY_TO_DPS_ID,
)

SUPPORT_FLAGS = SUPPORT_TARGET_HUMIDITY | SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE


class GoldairDehumidifier(ClimateEntity):
    """Representation of a Goldair WiFi dehumidifier."""

    def __init__(self, device):
        """Initialize the dehumidifier.
        Args:
            name (str): The device's name.
            device (GoldairTuyaDevice): The device API instance."""
        self._device = device

        self._support_flags = SUPPORT_FLAGS

        self._HUMIDITY_STEP = 5
        self._HUMIDITY_LIMITS = {"min": 30, "max": 80}

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
    def unique_id(self):
        """Return the unique id for this dehumidifier."""
        return self._device.unique_id

    @property
    def device_info(self):
        """Return device information about this dehumidifier."""
        return self._device.device_info

    @property
    def icon(self):
        """Return the icon to use in the frontend based on the device state."""
        if self.tank_full_or_missing:
            return "mdi:cup-water"
        elif self.defrosting:
            return "mdi:snowflake-melt"
        elif (
            self.hvac_mode is not HVAC_MODE_OFF
            and self.preset_mode is PRESET_DRY_CLOTHES
        ):
            return "mdi:tshirt-crew-outline"
        elif (
            self.hvac_mode is not HVAC_MODE_OFF and self.preset_mode is PRESET_AIR_CLEAN
        ):
            return "mdi:air-purifier"
        else:
            return "mdi:air-humidifier"

    @property
    def current_humidity(self):
        """Return the current reading of the humidity sensor."""
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_HUMIDITY])

    @property
    def min_humidity(self):
        """Return the minimum humidity setting."""
        return self._HUMIDITY_LIMITS["min"]

    @property
    def max_humidity(self):
        """Return the maximum humidity setting."""
        return self._HUMIDITY_LIMITS["max"]

    @property
    def target_humidity(self):
        """Return the current target humidity."""
        if self.preset_mode is PRESET_NORMAL:
            return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY])
        else:
            return None

    async def async_set_humidity(self, humidity):
        """Set the device's target humidity."""
        if self.preset_mode is not PRESET_NORMAL:
            raise ValueError(
                "Target humidity can only be changed while in Normal mode."
            )
        humidity = int(
            self._HUMIDITY_STEP * round(float(humidity) / self._HUMIDITY_STEP)
        )
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_TARGET_HUMIDITY], humidity
        )

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
            return GoldairTuyaDevice.get_key_for_value(HVAC_MODE_TO_DPS_MODE, dps_mode)
        else:
            return STATE_UNAVAILABLE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return list(HVAC_MODE_TO_DPS_MODE.keys())

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        dps_mode = HVAC_MODE_TO_DPS_MODE[hvac_mode]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE], dps_mode
        )

    @property
    def preset_mode(self):
        """Return current preset mode, ie Normal, Low, High, Dry Clothes, or Air Clean."""
        air_clean_on = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON])
        dps_mode = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE])

        if air_clean_on:
            return PRESET_AIR_CLEAN
        elif dps_mode is not None:
            return GoldairTuyaDevice.get_key_for_value(
                PRESET_MODE_TO_DPS_MODE, dps_mode
            )
        else:
            return None

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return list(PRESET_MODE_TO_DPS_MODE.keys()) + [PRESET_AIR_CLEAN]

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        if preset_mode == PRESET_AIR_CLEAN:
            await self._device.async_set_property(
                PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON], True
            )
            self._device.anticipate_property_value(
                PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH
            )
        else:
            dps_mode = PRESET_MODE_TO_DPS_MODE[preset_mode]
            await self._device.async_set_property(
                PROPERTY_TO_DPS_ID[ATTR_AIR_CLEAN_ON], False
            )
            await self._device.async_set_property(
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE], dps_mode
            )
            if preset_mode == PRESET_LOW:
                self._device.anticipate_property_value(
                    PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_LOW
                )
            elif preset_mode in [PRESET_HIGH, PRESET_DRY_CLOTHES]:
                self._device.anticipate_property_value(
                    PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], FAN_HIGH
                )

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
                return GoldairTuyaDevice.get_key_for_value(
                    FAN_MODE_TO_DPS_MODE, dps_mode
                )
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

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        if self.preset_mode != PRESET_NORMAL:
            raise ValueError(
                "Fan mode can only be changed while in Normal preset mode."
            )

        if fan_mode not in FAN_MODE_TO_DPS_MODE.keys():
            raise ValueError(f"Invalid fan mode: {fan_mode}")

        dps_mode = FAN_MODE_TO_DPS_MODE[fan_mode]
        await self._device.async_set_property(
            PROPERTY_TO_DPS_ID[ATTR_FAN_MODE], dps_mode
        )

    @property
    def tank_full_or_missing(self):
        error = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ERROR])
        return (
            GoldairTuyaDevice.get_key_for_value(ERROR_CODE_TO_DPS_CODE, error)
            == ERROR_TANK
        )

    @property
    def defrosting(self):
        return self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_DEFROSTING])

    @property
    def device_state_attributes(self):
        """Get additional attributes that HA doesn't naturally support."""
        error = self._device.get_property(PROPERTY_TO_DPS_ID[ATTR_ERROR])
        if error:
            error = GoldairTuyaDevice.get_key_for_value(
                ERROR_CODE_TO_DPS_CODE, error, error
            )

        return {ATTR_ERROR: error or None, ATTR_DEFROSTING: self.defrosting}

    async def async_update(self):
        await self._device.async_refresh()
