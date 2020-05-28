from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    FAN_HIGH,
    FAN_LOW,
    HVAC_MODE_DRY,
    HVAC_MODE_OFF,
)
from homeassistant.const import ATTR_TEMPERATURE

ATTR_TARGET_HUMIDITY = "target_humidity"
ATTR_AIR_CLEAN_ON = "air_clean_on"
ATTR_CHILD_LOCK = "child_lock"
ATTR_ERROR = "error"
ATTR_ERROR_CODE = "error_code"
ATTR_DISPLAY_OFF = "display_off"
ATTR_DEFROSTING = "defrosting"

PRESET_NORMAL = "Normal"
PRESET_LOW = "Low"
PRESET_HIGH = "High"
PRESET_DRY_CLOTHES = "Dry clothes"
PRESET_AIR_CLEAN = "Air clean"

ERROR_NONE = "OK"
ERROR_TANK = "Tank full or missing"

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: "1",
    ATTR_PRESET_MODE: "2",
    ATTR_TARGET_HUMIDITY: "4",
    ATTR_AIR_CLEAN_ON: "5",
    ATTR_FAN_MODE: "6",
    ATTR_CHILD_LOCK: "7",
    ATTR_ERROR: "11",
    ATTR_DISPLAY_OFF: "102",
    ATTR_TEMPERATURE: "103",
    ATTR_HUMIDITY: "104",
    ATTR_DEFROSTING: "105",
}

HVAC_MODE_TO_DPS_MODE = {HVAC_MODE_OFF: False, HVAC_MODE_DRY: True}
PRESET_MODE_TO_DPS_MODE = {
    PRESET_NORMAL: "0",
    PRESET_LOW: "1",
    PRESET_HIGH: "2",
    PRESET_DRY_CLOTHES: "3",
}
FAN_MODE_TO_DPS_MODE = {FAN_LOW: "1", FAN_HIGH: "3"}
ERROR_CODE_TO_DPS_CODE = {ERROR_NONE: 0, ERROR_TANK: 8}
