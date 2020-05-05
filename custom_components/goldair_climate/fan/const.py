from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_SLEEP,
    SWING_HORIZONTAL,
    SWING_OFF,
)

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_DISPLAY_ON = "display_on"

PRESET_NORMAL = "normal"

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: "1",
    ATTR_FAN_MODE: "2",
    ATTR_PRESET_MODE: "3",
    ATTR_SWING_MODE: "8",
    ATTR_DISPLAY_ON: "101",
}

HVAC_MODE_TO_DPS_MODE = {HVAC_MODE_OFF: False, HVAC_MODE_FAN_ONLY: True}
PRESET_MODE_TO_DPS_MODE = {
    PRESET_NORMAL: "normal",
    PRESET_ECO: "nature",
    PRESET_SLEEP: "sleep",
}
SWING_MODE_TO_DPS_MODE = {SWING_OFF: False, SWING_HORIZONTAL: True}
FAN_MODES = {
    PRESET_NORMAL: {
        1: "1",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "11",
        12: "12",
    },
    PRESET_ECO: {1: "4", 2: "8", 3: "12"},
    PRESET_SLEEP: {1: "4", 2: "8", 3: "12"},
}
