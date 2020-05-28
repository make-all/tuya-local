from homeassistant.components.switch import (
    ATTR_CURRENT_POWER_W,
)

ATTR_SWITCH = "switch"
ATTR_TIMER = "timer"
ATTR_CURRENT_A = "current"
ATTR_VOLTAGE_V = "voltage"

PROPERTY_TO_DPS_ID = {
    ATTR_SWITCH: "1",
    ATTR_TIMER: "2",
    ATTR_CURRENT_A: "4",
    ATTR_CURRENT_POWER_W: "5",
    ATTR_VOLTAGE_V: "6",
}
