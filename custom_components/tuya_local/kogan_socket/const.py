from homeassistant.components.switch import ATTR_CURRENT_POWER_W

ATTR_SWITCH = "switch"
ATTR_TIMER = "timer"
ATTR_CURRENT_A = "current_a"
ATTR_VOLTAGE_V = "voltage_v"
ATTR_ALT_TIMER = "alt_timer"
ATTR_ALT_CURRENT_A = "alt_currrent_a"
ATTR_ALT_CURRENT_POWER_W = "alt_power_w"
ATTR_ALT_VOLTAGE_V = "alt_voltage_v"

PROPERTY_TO_DPS_ID = {
    ATTR_SWITCH: "1",
    ATTR_TIMER: "2",
    ATTR_CURRENT_A: "4",
    ATTR_CURRENT_POWER_W: "5",
    ATTR_VOLTAGE_V: "6",
    ATTR_ALT_TIMER: "9",
    ATTR_ALT_CURRENT_A: "18",
    ATTR_ALT_CURRENT_POWER_W: "19",
    ATTR_ALT_VOLTAGE_V: "20",
}
