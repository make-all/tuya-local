"""
Platform for Goldair WiFi-connected heaters and panels.

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
from homeassistant.const import (CONF_NAME, CONF_HOST, ATTR_TEMPERATURE, TEMP_CELSIUS)
from homeassistant.components.climate import ATTR_OPERATION_MODE
from homeassistant.helpers.discovery import load_platform

VERSION = '0.0.2'
REQUIREMENTS = ['pytuya==7.0']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'goldair_climate'
DATA_GOLDAIR_CLIMATE = 'data_goldair_climate'


CONF_DEVICE_ID = 'device_id'
CONF_LOCAL_KEY = 'local_key'
CONF_TYPE = 'type'
CONF_TYPE_HEATER = 'heater'
CONF_CLIMATE = 'climate'
CONF_SENSOR = 'sensor'
CONF_CHILD_LOCK = 'child_lock'
CONF_DISPLAY_LIGHT = 'display_light'

ATTR_ON = 'on'
ATTR_TARGET_TEMPERATURE = 'target_temperature'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_FAULT = 'fault'
ATTR_POWER_LEVEL = 'power_level'
ATTR_TIMER_MINUTES = 'timer_minutes'
ATTR_TIMER_ON = 'timer_on'
ATTR_DISPLAY_ON = 'display_on'
ATTR_POWER_MODE = 'power_mode'
ATTR_ECO_TARGET_TEMPERATURE = 'eco_' + ATTR_TARGET_TEMPERATURE

STATE_COMFORT = 'Comfort'
STATE_ECO = 'Eco'
STATE_ANTI_FREEZE = 'Anti-freeze'

GOLDAIR_PROPERTY_TO_DPS_ID = {
    ATTR_ON: '1',
    ATTR_TARGET_TEMPERATURE: '2',
    ATTR_TEMPERATURE: '3',
    ATTR_OPERATION_MODE: '4',
    ATTR_CHILD_LOCK: '6',
    ATTR_FAULT: '12',
    ATTR_POWER_LEVEL: '101',
    ATTR_TIMER_MINUTES: '102',
    ATTR_TIMER_ON: '103',
    ATTR_DISPLAY_ON: '104',
    ATTR_POWER_MODE: '105',
    ATTR_ECO_TARGET_TEMPERATURE: '106'
}

GOLDAIR_MODE_TO_DPS_MODE = {
    STATE_COMFORT: 'C',
    STATE_ECO: 'ECO',
    STATE_ANTI_FREEZE: 'AF'
}
GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL = {
    'Stop': 'stop',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    'Auto': 'auto'
}
GOLDAIR_POWER_MODES = ['auto', 'user']

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_LOCAL_KEY): cv.string,
    vol.Required(CONF_TYPE): vol.In([CONF_TYPE_HEATER]),
    vol.Optional(CONF_CLIMATE, default=True): cv.boolean,
    vol.Optional(CONF_SENSOR, default=False): cv.boolean,
    vol.Optional(CONF_DISPLAY_LIGHT, default=False): cv.boolean,
    vol.Optional(CONF_CHILD_LOCK, default=False): cv.boolean
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(cv.ensure_list, [PLATFORM_SCHEMA])
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    hass.data[DOMAIN] = {}
    for device_config in config.get(DOMAIN, []):
        host = device_config.get(CONF_HOST)

        device = GoldairHeaterDevice(
            device_config.get(CONF_NAME),
            device_config.get(CONF_DEVICE_ID),
            device_config.get(CONF_HOST),
            device_config.get(CONF_LOCAL_KEY)
        )
        hass.data[DOMAIN][host] = device

        if device_config.get(CONF_TYPE) == CONF_TYPE_HEATER:
            discovery_info = {'host': host, 'type': 'heater'}
            if device_config.get(CONF_CLIMATE):
                load_platform(hass, 'climate', DOMAIN, discovery_info, config)
            if device_config.get(CONF_SENSOR):
                load_platform(hass, 'sensor', DOMAIN, discovery_info, config)
            if device_config.get(CONF_DISPLAY_LIGHT):
                load_platform(hass, 'light', DOMAIN, discovery_info, config)
            if device_config.get(CONF_CHILD_LOCK):
                load_platform(hass, 'lock', DOMAIN, discovery_info, config)

    return True


class GoldairHeaterDevice(object):
    def __init__(self, name, dev_id, address, local_key):
        """
        Represents a Goldair Heater device.

        Args:
            dev_id (str): The device id.
            address (str): The network address.
            local_key (str): The encryption key.
        """
        import pytuya
        self._name = name
        self._api = pytuya.Device(dev_id, address, local_key, 'device')

        self._fixed_properties = {}
        self._reset_cached_state()

        self._TEMPERATURE_UNIT = TEMP_CELSIUS
        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {
            STATE_COMFORT: {
                'min': 5,
                'max': 35
            },
            STATE_ECO: {
                'min': 5,
                'max': 21
            }
        }

        # API calls to update Goldair heaters are asynchronous and non-blocking. This means
        # you can send a change and immediately request an updated state (like HA does),
        # but because it has not yet finished processing you will be returned the old state.
        # The solution is to keep a temporary list of changed properties that we can overlay
        # onto the state while we wait for the board to update its switches.
        self._FAKE_IT_TIL_YOU_MAKE_IT_TIMEOUT = 10
        self._CACHE_TIMEOUT = 20
        self._CONNECTION_ATTEMPTS = 2
        self._lock = Lock()

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._get_cached_state()[ATTR_ON]

    def turn_on(self):
        self._set_properties({ATTR_ON: True})

    def turn_off(self):
        self._set_properties({ATTR_ON: False})

    @property
    def temperature_unit(self):
        return self._TEMPERATURE_UNIT

    @property
    def target_temperature(self):
        state = self._get_cached_state()
        if self.operation_mode == STATE_COMFORT:
            return state[ATTR_TARGET_TEMPERATURE]
        elif self.operation_mode == STATE_ECO:
            return state[ATTR_ECO_TARGET_TEMPERATURE]
        else:
            return None

    @property
    def target_temperature_step(self):
        return self._TEMPERATURE_STEP

    @property
    def min_target_teperature(self):
        if self.operation_mode and self.operation_mode != STATE_ANTI_FREEZE:
            return self._TEMPERATURE_LIMITS[self.operation_mode]['min']
        else:
            return None

    @property
    def max_target_temperature(self):
        if self.operation_mode and self.operation_mode != STATE_ANTI_FREEZE:
            return self._TEMPERATURE_LIMITS[self.operation_mode]['max']
        else:
            return None

    def set_target_temperature(self, target_temperature):
        target_temperature = int(round(target_temperature))
        operation_mode = self.operation_mode

        if operation_mode == STATE_ANTI_FREEZE:
            raise ValueError('You cannot set the temperature in Anti-freeze mode.')

        limits = self._TEMPERATURE_LIMITS[operation_mode]
        if not limits['min'] <= target_temperature <= limits['max']:
            raise ValueError(
                f'Target temperature ({target_temperature}) must be between '
                f'{limits["min"]} and {limits["max"]}'
            )

        if operation_mode == STATE_COMFORT:
            self._set_properties({ATTR_TARGET_TEMPERATURE: target_temperature})
        elif operation_mode == STATE_ECO:
            self._set_properties({ATTR_ECO_TARGET_TEMPERATURE: target_temperature})

    @property
    def current_temperature(self):
        return self._get_cached_state()[ATTR_TEMPERATURE]

    @property
    def operation_mode(self):
        return self._get_cached_state()[ATTR_OPERATION_MODE]

    @property
    def operation_mode_list(self):
        return list(GOLDAIR_MODE_TO_DPS_MODE.keys())

    def set_operation_mode(self, new_mode):
        if new_mode not in GOLDAIR_MODE_TO_DPS_MODE:
            raise ValueError(f'Invalid mode: {new_mode}')
        self._set_properties({ATTR_OPERATION_MODE: new_mode})

    @property
    def is_child_locked(self):
        return self._get_cached_state()[ATTR_CHILD_LOCK]

    def enable_child_lock(self):
        self._set_properties({ATTR_CHILD_LOCK: True})

    def disable_child_lock(self):
        self._set_properties({ATTR_CHILD_LOCK: False})

    @property
    def is_faulted(self):
        return self._get_cached_state()[ATTR_FAULT]

    @property
    def power_level(self):
        power_mode = self._get_cached_state()[ATTR_POWER_MODE]
        if power_mode == 'user':
            return self._get_cached_state()[ATTR_POWER_LEVEL]
        elif power_mode == 'auto':
            return 'Auto'
        else:
            return None

    @property
    def power_level_list(self):
        return list(GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL.keys())

    def set_power_level(self, new_level):
        if new_level not in GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL.keys():
            raise ValueError(f'Invalid power level: {new_level}')
        self._set_properties({ATTR_POWER_LEVEL: new_level})

    @property
    def timer_timeout_in_minutes(self):
        return self._get_cached_state()[ATTR_TIMER_MINUTES]

    @property
    def is_timer_on(self):
        return self._get_cached_state()[ATTR_TIMER_ON]

    def start_timer(self, minutes):
        self._set_properties({
            ATTR_TIMER_ON: True,
            ATTR_TIMER_MINUTES: minutes
        })

    def stop_timer(self):
        self._set_properties({ATTR_TIMER_ON: False})

    @property
    def is_display_on(self):
        return self._get_cached_state()[ATTR_DISPLAY_ON]

    def turn_display_on(self):
        self._set_properties({ATTR_DISPLAY_ON: True})

    def turn_display_off(self):
        self._set_properties({ATTR_DISPLAY_ON: False})

    @property
    def power_mode(self):
        return self._get_cached_state()[ATTR_POWER_MODE]

    def set_power_mode(self, new_mode):
        if new_mode not in GOLDAIR_POWER_MODES:
            raise ValueError(f'Invalid user mode: {new_mode}')
        self._set_properties({ATTR_POWER_MODE: new_mode})

    @property
    def eco_target_temperature(self):
        return self._get_cached_state()[ATTR_ECO_TARGET_TEMPERATURE]

    def set_eco_target_temperature(self, eco_target_temperature):
        self._set_properties({ATTR_ECO_TARGET_TEMPERATURE: eco_target_temperature})

    def set_fixed_properties(self, fixed_properties):
        self._fixed_properties = fixed_properties
        set_fixed_properties = Timer(10, lambda: self._set_properties(self._fixed_properties))
        set_fixed_properties.start()

    def refresh(self):
        now = time()
        cached_state = self._get_cached_state()
        if now - cached_state['updated_at'] >= self._CACHE_TIMEOUT:
            self._retry_on_failed_connection(lambda: self._refresh_cached_state(), 'Failed to refresh device state.')

    def _reset_cached_state(self):
        self._cached_state = {
            ATTR_ON: None,
            ATTR_TARGET_TEMPERATURE: None,
            ATTR_TEMPERATURE: None,
            ATTR_OPERATION_MODE: None,
            ATTR_CHILD_LOCK: None,
            ATTR_FAULT: None,
            ATTR_POWER_LEVEL: None,
            ATTR_TIMER_MINUTES: None,
            ATTR_TIMER_ON: None,
            ATTR_DISPLAY_ON: None,
            ATTR_POWER_MODE: None,
            ATTR_ECO_TARGET_TEMPERATURE: None,
            'updated_at': 0
        }
        self._pending_updates = {}

    def _refresh_cached_state(self):
        new_state = self._api.status()
        self._update_cached_state_from_dps(new_state['dps'])
        _LOGGER.info(f'refreshed device state: {json.dumps(new_state)}')
        _LOGGER.debug(f'new cache state: {json.dumps(self._cached_state)}')
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
        new_state = GoldairHeaterDevice._generate_dps_payload_for_properties(pending_properties)
        payload = self._api.generate_payload('set', new_state)

        _LOGGER.debug(f'sending updated properties: {json.dumps(pending_properties)}')
        _LOGGER.info(f'sending dps update: {json.dumps(new_state)}')

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

    def _update_cached_state_from_dps(self, dps):
        now = time()

        for key, dps_id in GOLDAIR_PROPERTY_TO_DPS_ID.items():
            if dps_id in dps:
                value = dps[dps_id]
                if dps_id == GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_OPERATION_MODE]:
                    self._cached_state[key] = GoldairHeaterDevice._get_key_for_value(GOLDAIR_MODE_TO_DPS_MODE, value)
                elif dps_id == GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]:
                    self._cached_state[key] = GoldairHeaterDevice._get_key_for_value(GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL, value)
                else:
                    self._cached_state[key] = value
                self._cached_state['updated_at'] = now

    @staticmethod
    def _generate_dps_payload_for_properties(properties):
        dps = {}

        for key, dps_id in GOLDAIR_PROPERTY_TO_DPS_ID.items():
            if key in properties:
                value = properties[key]
                if dps_id == GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_OPERATION_MODE]:
                    dps[dps_id] = GOLDAIR_MODE_TO_DPS_MODE[value]
                elif dps_id == GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]:
                    dps[dps_id] = GOLDAIR_POWER_LEVEL_TO_DPS_LEVEL[value]
                else:
                    dps[dps_id] = value

        return dps

    @staticmethod
    def _get_key_for_value(obj, value):
        keys = list(obj.keys())
        values = list(obj.values())
        return keys[values.index(value)]
