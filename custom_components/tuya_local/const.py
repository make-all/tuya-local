from datetime import timedelta

DOMAIN = "tuya_local"

CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_TYPE = "type"
CONF_CLIMATE = "climate"
CONF_FAN = "fan"
CONF_LIGHT = "light"
CONF_LOCK = "lock"
CONF_SWITCH = "switch"
CONF_HUMIDIFIER = "humidifier"
API_PROTOCOL_VERSIONS = [3.3, 3.1]
SCAN_INTERVAL = timedelta(seconds=30)
