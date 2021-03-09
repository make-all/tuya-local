from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_SWING_MODE,
)
from homeassistant.const import ATTR_TEMPERATURE

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_DISPLAY_OFF = "display_off"
ATTR_POWER_LEVEL = "power_level"
ATTR_TIMER_HR = "timer_hours"
ATTR_TIMER_REMAIN = "timer_remain"
ATTR_OPEN_WINDOW_DETECT = "open_window_detect"

POWER_LEVEL_AUTO = "auto"
POWER_LEVEL_FANONLY = "off"
PRESET_FAN = "Fan"
PRESET_AUTO = "Auto"

POWER_LEVEL_TO_DPS_LEVEL = {
    PRESET_FAN: POWER_LEVEL_FANONLY,
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    PRESET_AUTO: POWER_LEVEL_AUTO,
}

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: "1",
    ATTR_TARGET_TEMPERATURE: "2",
    ATTR_TEMPERATURE: "3",
    ATTR_POWER_LEVEL: "5",
    ATTR_DISPLAY_OFF: "10",
    ATTR_TIMER_HR: "11",
    ATTR_TIMER_REMAIN: "12",
    ATTR_OPEN_WINDOW_DETECT: "101",
    ATTR_SWING_MODE: "102",
}
