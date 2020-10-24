from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
)
from homeassistant.const import ATTR_TEMPERATURE

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_ERROR = "error"

PRESET_LOW = "Low"
PRESET_HIGH = "High"
PRESET_ANTIFREEZE = "Anti-freeze"

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: "1",
    ATTR_TARGET_TEMPERATURE: "2",
    ATTR_TEMPERATURE: "3",
    ATTR_PRESET_MODE: "4",
    ATTR_ERROR: "12",
}

HVAC_MODE_TO_DPS_MODE = {HVAC_MODE_OFF: False, HVAC_MODE_HEAT: True}
PRESET_MODE_TO_DPS_MODE = {
    PRESET_LOW: "low",
    PRESET_HIGH: "high",
    PRESET_ANTIFREEZE: "af",
}
