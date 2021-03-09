from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
)
from homeassistant.const import ATTR_TEMPERATURE

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_TEMP_UNIT = "temperature_unit"
ATTR_POWER_LEVEL = "power_level"
ATTR_OPERATING_MODE = "operating_mode"

PROPERTY_TO_DPS_ID = {
    ATTR_HVAC_MODE: "1",
    ATTR_TEMPERATURE: "102",
    ATTR_TEMP_UNIT: "103",
    ATTR_POWER_LEVEL: "104",
    ATTR_OPERATING_MODE: "105",
    ATTR_TARGET_TEMPERATURE: "106",
    ATTR_PRESET_MODE: "117",
}

HVAC_MODE_TO_DPS_MODE = {HVAC_MODE_OFF: False, HVAC_MODE_HEAT: True}
PRESET_SILENT = "Silent"
PRESET_SMART = "Smart"
PRESET_MODE_TO_DPS_MODE = {PRESET_SILENT: False, PRESET_SMART: True}
