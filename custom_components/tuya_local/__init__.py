"""
Platform for Tuya WiFi-connected devices.

Based on nikrolls/homeassistant-goldair-climate for Goldair branded devices.
Based on sean6541/tuya-homeassistant for service call logic, and TarxBoy's
investigation into Goldair's tuyapi statuses
https://github.com/codetheweb/tuyapi/issues/31.
"""
from time import time
from threading import Timer, Lock
import logging
import json
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_NAME, CONF_HOST, TEMP_CELSIUS)
from homeassistant.helpers.discovery import load_platform

VERSION = '0.0.8'

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'tuya_local'
DATA_TUYA_LOCAL = 'data_tuya_local'

API_PROTOCOL_VERSIONS = [3.3, 3.1]

CONF_DEVICE_ID = 'device_id'
CONF_LOCAL_KEY = 'local_key'
CONF_TYPE = 'type'
CONF_TYPE_HEATER = 'heater'
CONF_TYPE_DEHUMIDIFIER = 'dehumidifier'
CONF_TYPE_FAN = 'fan'
CONF_TYPE_KOGAN_HEATER = 'kogan_heater'
CONF_CLIMATE = 'climate'
CONF_DISPLAY_LIGHT = 'display_light'
CONF_CHILD_LOCK = 'child_lock'
CONF_TANK_FULL = 'tank_full'

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_LOCAL_KEY): cv.string,
    vol.Required(CONF_TYPE): vol.In([CONF_TYPE_HEATER, CONF_TYPE_DEHUMIDIFIER, CONF_TYPE_FAN, CONF_TYPE_KOGAN_HEATER]),
    vol.Optional(CONF_CLIMATE, default=True): cv.boolean,
    vol.Optional(CONF_DISPLAY_LIGHT, default=False): cv.boolean,
    vol.Optional(CONF_CHILD_LOCK, default=False): cv.boolean,
    vol.Optional(CONF_TANK_FULL, default=False): cv.boolean,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(cv.ensure_list, [PLATFORM_SCHEMA])
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    hass.data[DOMAIN] = {}
    for device_config in config.get(DOMAIN, []):
        host = device_config.get(CONF_HOST)

        device = TuyaLocalDevice(
            device_config.get(CONF_NAME),
            device_config.get(CONF_DEVICE_ID),
            device_config.get(CONF_HOST),
            device_config.get(CONF_LOCAL_KEY)
        )
        hass.data[DOMAIN][host] = device
        discovery_info = {CONF_HOST: host, CONF_TYPE: device_config.get(CONF_TYPE)}

        if device_config.get(CONF_CLIMATE) == True:
            load_platform(hass, 'climate', DOMAIN, discovery_info, config)
        if device_config.get(CONF_DISPLAY_LIGHT) == True:
            load_platform(hass, 'light', DOMAIN, discovery_info, config)
        if device_config.get(CONF_CHILD_LOCK) == True:
            load_platform(hass, 'lock', DOMAIN, discovery_info, config)
        if device_config.get(CONF_TANK_FULL) == True:
            load_platform(hass, 'binary_sensor', DOMAIN, discovery_info, config)

    return True


class TuyaLocalDevice(object):
    def __init__(self, name, dev_id, address, local_key):
        """
        Represents a Tuya-based device.

        Args:
            dev_id (str): The device id.
            address (str): The network address.
            local_key (str): The encryption key.
        """
        import pytuya
        self._name = name
        self._api_protocol_version_index = None
        self._api = pytuya.Device(dev_id, address, local_key, 'device')
        self._rotate_api_protocol_version()

        self._fixed_properties = {}
        self._reset_cached_state()

        self._TEMPERATURE_UNIT = TEMP_CELSIUS

        # API calls to update Tuya devices are asynchronous and non-blocking. This means
        # you can send a change and immediately request an updated state (like HA does),
        # but because it has not yet finished processing you will be returned the old state.
        # The solution is to keep a temporary list of changed properties that we can overlay
        # onto the state while we wait for the board to update its switches.
        self._FAKE_IT_TIL_YOU_MAKE_IT_TIMEOUT = 10
        self._CACHE_TIMEOUT = 20
        self._CONNECTION_ATTEMPTS = 4
        self._lock = Lock()

    @property
    def name(self):
        return self._name

    @property
    def temperature_unit(self):
        return self._TEMPERATURE_UNIT

    def set_fixed_properties(self, fixed_properties):
        self._fixed_properties = fixed_properties
        set_fixed_properties = Timer(10, lambda: self._set_properties(self._fixed_properties))
        set_fixed_properties.start()

    def refresh(self):
        now = time()
        cached_state = self._get_cached_state()
        if now - cached_state['updated_at'] >= self._CACHE_TIMEOUT:
            self._cached_state['updated_at'] = time()
            self._retry_on_failed_connection(lambda: self._refresh_cached_state(), f'Failed to refresh device state for {self.name}.')

    def get_property(self, dps_id):
        cached_state = self._get_cached_state()
        if dps_id in cached_state:
            return cached_state[dps_id]
        else:
            return None

    def set_property(self, dps_id, value):
        self._set_properties({dps_id: value})

    def anticipate_property_value(self, dps_id, value):
        """
        Update a value in the cached state only. This is good for when you know the device will reflect a new state in
        the next update, but don't want to wait for that update for the device to represent this state.

        The anticipated value will be cleared with the next update.
        """
        self._cached_state[dps_id] = value

    def _reset_cached_state(self):
        self._cached_state = {
            'updated_at': 0
        }
        self._pending_updates = {}

    def _refresh_cached_state(self):
        new_state = self._api.status()
        self._cached_state = new_state['dps']
        self._cached_state['updated_at'] = time()
        _LOGGER.info(f'refreshed device state: {json.dumps(new_state)}')
        _LOGGER.debug(f'new cache state (including pending properties): {json.dumps(self._get_cached_state())}')

    def _set_properties(self, properties):
        if len(properties) == 0:
            return

        self._add_properties_to_pending_updates(properties)
        self._debounce_sending_updates()

    def _add_properties_to_pending_updates(self, properties):
        now = time()
        properties = {**properties, **self._fixed_properties}

        pending_updates = self._get_pending_updates()
        for key, value in properties.items():
            pending_updates[key] = {
                'value': value,
                'updated_at': now
            }

        _LOGGER.debug(f'new pending updates: {json.dumps(self._pending_updates)}')

    def _debounce_sending_updates(self):
        try:
            self._debounce.cancel()
        except AttributeError:
            pass
        self._debounce = Timer(1, self._send_pending_updates)
        self._debounce.start()

    def _send_pending_updates(self):
        pending_properties = self._get_pending_properties()
        payload = self._api.generate_payload('set', pending_properties)

        _LOGGER.info(f'sending dps update: {json.dumps(pending_properties)}')

        self._retry_on_failed_connection(lambda: self._send_payload(payload), 'Failed to update device state.')

    def _send_payload(self, payload):
        try:
            self._lock.acquire()
            self._api._send_receive(payload)
            self._cached_state['updated_at'] = 0
            now = time()
            pending_updates = self._get_pending_updates()
            for key, value in pending_updates.items():
                pending_updates[key]['updated_at'] = now
        finally:
            self._lock.release()

    def _retry_on_failed_connection(self, func, error_message):
        for i in range(self._CONNECTION_ATTEMPTS):
            try:
                func()
            except:
                if i + 1 == self._CONNECTION_ATTEMPTS:
                    self._reset_cached_state()
                    _LOGGER.error(error_message)
                else:
                    self._rotate_api_protocol_version()

    def _get_cached_state(self):
        cached_state = self._cached_state.copy()
        _LOGGER.debug(f'pending updates: {json.dumps(self._get_pending_updates())}')
        return {**cached_state, **self._get_pending_properties()}

    def _get_pending_properties(self):
        return {key: info['value'] for key, info in self._get_pending_updates().items()}

    def _get_pending_updates(self):
        now = time()
        self._pending_updates = {key: value for key, value in self._pending_updates.items()
                                 if now - value['updated_at'] < self._FAKE_IT_TIL_YOU_MAKE_IT_TIMEOUT}
        return self._pending_updates

    def _rotate_api_protocol_version(self):
        if self._api_protocol_version_index is None:
            self._api_protocol_version_index = 0
        else:
            self._api_protocol_version_index += 1

        if self._api_protocol_version_index >= len(API_PROTOCOL_VERSIONS):
            self._api_protocol_version_index = 0

        new_version = API_PROTOCOL_VERSIONS[self._api_protocol_version_index]
        _LOGGER.info(f'Setting protocol version for {self.name} to {new_version}.')
        self._api.set_version(new_version)

    @staticmethod
    def get_key_for_value(obj, value):
        keys = list(obj.keys())
        values = list(obj.values())
        return keys[values.index(value)]
