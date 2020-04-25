from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.components.climate.const import (
    ATTR_FAN_MODE, ATTR_HUMIDITY, ATTR_HVAC_MODE, ATTR_PRESET_MODE, FAN_LOW, FAN_HIGH, HVAC_MODE_OFF, HVAC_MODE_DRY
)

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
