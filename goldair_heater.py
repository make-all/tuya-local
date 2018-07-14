"""
Platform to control Goldair WiFi-connected digital inverter heaters.

Based on sean6541/tuya-homeassistant for service call logic, and TarxBoy's
investigation into Goldair's tuyapi statuses
https://github.com/codetheweb/tuyapi/issues/31.
"""
import logging
import json

import voluptuous as vol
from homeassistant.components.climate import (
    ClimateDevice, PLATFORM_SCHEMA,
    ATTR_OPERATION_MODE, ATTR_TEMPERATURE,
    SUPPORT_ON_OFF, SUPPORT_TARGET_TEMPERATURE, SUPPORT_OPERATION_MODE)
from homeassistant.const import (
    CONF_NAME, CONF_HOST, STATE_ON, STATE_OFF, STATE_UNAVAILABLE, TEMP_CELSIUS
)
import homeassistant.helpers.config_validation as cv
from threading import Lock

REQUIREMENTS = ['pytuya==7.0']

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE_ID = 'device_id'
CONF_LOCAL_KEY = 'local_key'
CONF_ADDITIONAL_PROPERTIES = 'additional_properties'
CONF_POWER_LEVEL = 'power_level'
CONF_CHILD_LOCK = 'child_lock'
CONF_DISPLAY_ON = 'display_on'

ATTR_ON = 'on'
ATTR_TARGET_TEMPERATURE = 'target_temperature'

STATE_COMFORT = 'Comfort'
STATE_ECO = 'Eco'
STATE_ANTI_FREEZE = 'Anti-freeze'

ATTR_CHILD_LOCK = 'child_lock'
ATTR_FAULT = 'fault'
ATTR_POWER_LEVEL = 'power_level'
ATTR_TIMER_MINUTES = 'timer_minutes'
ATTR_TIMER_ON = 'timer_on'
ATTR_DISPLAY_ON = 'display_on'
ATTR_USER_MODE = 'user_mode' # not sure what this does
ATTR_ECO_TARGET_TEMPERATURE = 'eco_' + ATTR_TARGET_TEMPERATURE

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
    ATTR_USER_MODE: '105', # not sure what this does
    ATTR_ECO_TARGET_TEMPERATURE: '106'
}

GOLDAIR_MODE_TO_DPS_MODE = {
    STATE_COMFORT: 'C',
    STATE_ECO: 'ECO',
    STATE_ANTI_FREEZE: 'AF'
}
GOLDAIR_POWER_LEVELS = ['stop', '1', '2', '3', '4', '5', 'auto']
GOLDAIR_USER_MODES = ['auto', 'user'] # not sure what this does

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_LOCAL_KEY): cv.string,
    vol.Optional(CONF_POWER_LEVEL): vol.All(vol.Coerce(str), vol.In(GOLDAIR_POWER_LEVELS)),
    vol.Optional(CONF_CHILD_LOCK): cv.boolean,
    vol.Optional(CONF_DISPLAY_ON): cv.boolean
})

SUPPORT_FLAGS =  SUPPORT_ON_OFF | SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Goldair WiFi heater."""
    device = GoldairHeaterDevice(
        config.get(CONF_DEVICE_ID),
        config.get(CONF_HOST),
        config.get(CONF_LOCAL_KEY)
    )

    fixed_properties = {
        ATTR_POWER_LEVEL: str(config.get(CONF_POWER_LEVEL)),
        ATTR_CHILD_LOCK: config.get(CONF_CHILD_LOCK),
        ATTR_DISPLAY_ON: config.get(CONF_DISPLAY_ON)
    }
    fixed_properties = {k: v for k, v in fixed_properties.items() if v is not None}
    if len(fixed_properties) > 0:
        device.set_fixed_properties(fixed_properties)

    add_devices([
        GoldairHeater(config.get(CONF_NAME), device)
    ])

class GoldairHeater(ClimateDevice):
    """Representation of a Goldair WiFi heater."""

    def __init__(self, name, device):
        """Initialize the heater.
        Args:
            name (str): The device's name.
            device (GoldairHeaterDevice): The device API instance."""
        self._name = name
        self._device = device

        self._support_flags = SUPPORT_FLAGS

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def state(self):
        """Return the current state."""
        if self._device.is_on is None:
            return STATE_UNAVAILABLE
        else:
            return super().state

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self._device.is_on

    def turn_on(self):
        """Turn on."""
        self._device.turn_on()

    def turn_off(self):
        """Turn off."""
        self._device.turn_off()

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._device.target_temperature_step

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._device.min_target_teperature

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._device.max_target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._device.set_target_temperature(kwargs.get(ATTR_TEMPERATURE))
        if kwargs.get(ATTR_OPERATION_MODE) is not None:
            self._device.set_operation_mode(kwargs.get(ATTR_OPERATION_MODE))

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.current_temperature

    @property
    def current_operation(self):
        """Return current operation, ie Comfort, Eco, Anti-freeze."""
        return self._device.operation_mode

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._device.operation_mode_list

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        self._device.set_operation_mode(operation_mode)

    def update(self):
        self._device.refresh()


import pytuya
from time import time
from threading import Timer

class GoldairHeaterDevice(pytuya.Device):
    def __init__(self, dev_id, address, local_key):
        """
        Represents a Goldair Heater device.

        Args:
            dev_id (str): The device id.
            address (str): The network address.
            local_key (str): The encryption key.
        """
        super().__init__(dev_id, address, local_key, 'device')
        
        self._fixed_properties = {}
        self._reset_cached_state()

        self._TEMPERATURE_UNIT = TEMP_CELSIUS
        self._TEMPERATURE_STEP = 1
        self._MIN_TARGET_TEMPERATURE = 5
        self._MAX_TARGET_TEMPERATURE = 35

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
        return self._get_cached_state()[ATTR_TARGET_TEMPERATURE]

    @property
    def target_temperature_step(self):
        return self._TEMPERATURE_STEP

    @property
    def min_target_teperature(self):
        return self._MIN_TARGET_TEMPERATURE

    @property
    def max_target_temperature(self):
        return self._MAX_TARGET_TEMPERATURE
    
    def set_target_temperature(self, target_temperature):
        target_temperature = int(round(target_temperature))
        if not self._MIN_TARGET_TEMPERATURE <= target_temperature <= self._MAX_TARGET_TEMPERATURE:
            raise ValueError(
                f'Target temperature ({target_temperature}) must be between '
                f'{self._MIN_TARGET_TEMPERATURE} and {self._MAX_TARGET_TEMPERATURE}'
            ) 
        self._set_properties({ATTR_TARGET_TEMPERATURE: target_temperature})
    
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
        if not new_mode in GOLDAIR_MODE_TO_DPS_MODE:
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
        return self._get_cached_state()[ATTR_POWER_LEVEL]

    def set_power_level(self, new_level):
        if not new_level in GOLDAIR_POWER_LEVELS:
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
    def user_mode(self):
        return self._get_cached_state()[ATTR_USER_MODE]

    def set_user_mode(self, new_mode):
        if not new_mode in GOLDAIR_USER_MODES:
            raise ValueError(f'Invalid user mode: {new_mode}')
        self._set_properties({ATTR_USER_MODE: new_mode})

    @property
    def eco_target_temperature(self):
        return self._get_cached_state()[ATTR_ECO_TARGET_TEMPERATURE]
    
    def set_eco_target_temperature(self, eco_target_temperature):
        self._set_properties({ATTR_ECO_TARGET_TEMPERATURE})

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
            ATTR_USER_MODE: None,
            ATTR_ECO_TARGET_TEMPERATURE: None,
            'updated_at': 0
        }
        self._pending_updates = {}

    def _refresh_cached_state(self):
        new_state = self.status()
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
        new_state = self._generate_dps_payload_for_properties(pending_properties)
        payload = self.generate_payload('set', new_state)

        _LOGGER.debug(f'sending updated properties: {json.dumps(pending_properties)}')
        _LOGGER.info(f'sending dps update: {json.dumps(new_state)}')

        self._retry_on_failed_connection(lambda: self._send_payload(payload), 'Failed to update device state.')

    def _send_payload(self, payload):
        try:
            self._lock.acquire()
            self._send_receive(payload)
            now = time()
            pending_updates = self._get_pending_updates()
            for key, value in properties.items():
                if key in pending_updates:
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
                    self._cached_state[key] = self._get_key_for_value(GOLDAIR_MODE_TO_DPS_MODE, value)
                else:
                    self._cached_state[key] = value
                self._cached_state['updated_at'] = now

    def _generate_dps_payload_for_properties(self, properties):
        dps = {}

        for key, dps_id in GOLDAIR_PROPERTY_TO_DPS_ID.items():
            if key in properties:
                value = properties[key]
                if dps_id == GOLDAIR_PROPERTY_TO_DPS_ID[ATTR_OPERATION_MODE]:
                    dps[dps_id] = GOLDAIR_MODE_TO_DPS_MODE[value]
                else:
                    dps[dps_id] = value

        return dps

    def _get_key_for_value(self, obj, value):
        keys = list(obj.keys())
        values = list(obj.values())
        return keys[values.index(value)]
