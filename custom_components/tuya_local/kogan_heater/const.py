from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
)
from homeassistant.const import ATTR_TEMPERATURE

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_CHILD_LOCK = "child_lock"
ATTR_TIMER = "timer"

PRESET_LOW = "LOW"
PRESET_HIGH = "HIGH"

PROPERTY_TO_DPS_ID = {
    ATTR_TARGET_TEMPERATURE: "2",
    ATTR_TEMPERATURE: "3",
    ATTR_PRESET_MODE: "4",
    ATTR_CHILD_LOCK: "6",
    ATTR_HVAC_MODE: "7",
    ATTR_TIMER: "8",
}

HVAC_MODE_TO_DPS_MODE = {HVAC_MODE_OFF: False, HVAC_MODE_HEAT: True}
PRESET_MODE_TO_DPS_MODE = {
    PRESET_LOW: "Low",
    PRESET_HIGH: "High",
}
