from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
)
from homeassistant.const import ATTR_TEMPERATURE

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_CHILD_LOCK = "child_lock"
ATTR_ERROR = "error"
ATTR_ERROR_CODE = "error_code"
ATTR_POWER_MODE_AUTO = "auto"
ATTR_POWER_MODE_USER = "user"
ATTR_POWER_LEVEL = "power_level"
ATTR_DISPLAY_ON = "display_on"
ATTR_POWER_MODE = "power_mode"
ATTR_ECO_TARGET_TEMPERATURE = "eco_" + ATTR_TARGET_TEMPERATURE

STATE_COMFORT = "Comfort"
STATE_ECO = "Eco"
STATE_ANTI_FREEZE = "Anti-freeze"

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: "1",
    ATTR_TARGET_TEMPERATURE: "2",
    ATTR_TEMPERATURE: "3",
    ATTR_PRESET_MODE: "4",
    ATTR_CHILD_LOCK: "6",
    ATTR_ERROR: "12",
    ATTR_POWER_LEVEL: "101",
    ATTR_DISPLAY_ON: "104",
    ATTR_POWER_MODE: "105",
    ATTR_ECO_TARGET_TEMPERATURE: "106",
}

HVAC_MODE_TO_DPS_MODE = {HVAC_MODE_OFF: False, HVAC_MODE_HEAT: True}
PRESET_MODE_TO_DPS_MODE = {
    STATE_COMFORT: "C",
    STATE_ECO: "ECO",
    STATE_ANTI_FREEZE: "AF",
}

POWER_LEVEL_STOP = "stop"
POWER_LEVEL_AUTO = "auto"
POWER_LEVEL_TO_DPS_LEVEL = {
    "Stop": POWER_LEVEL_STOP,
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "Auto": POWER_LEVEL_AUTO,
}
