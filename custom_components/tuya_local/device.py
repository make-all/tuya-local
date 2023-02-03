"""
API for Tuya Local devices.
"""

import asyncio
import json
import logging
import tinytuya
from threading import Lock
from time import time


from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant

from .const import (
    API_PROTOCOL_VERSIONS,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    DOMAIN,
)
from .helpers.device_config import possible_matches


_LOGGER = logging.getLogger(__name__)


def non_json(input):
    """Handler for json_dumps when used for debugging."""
    return f"Non-JSON: ({input})"


class TuyaLocalDevice(object):
    def __init__(
        self,
        name,
        dev_id,
        address,
        local_key,
        protocol_version,
        hass: HomeAssistant,
        poll_only=False,
    ):
        """
        Represents a Tuya-based device.

        Args:
            dev_id (str): The device id.
            address (str): The network address.
            local_key (str): The encryption key.
            protocol_version (str | number): The protocol version.
            hass (HomeAssistant): The Home Assistant instance.
            poll_only (bool): True if the device should be polled only
        """
        self._name = name
        self._children = []
        self._running = False
        self._shutdown_listener = None
        self._startup_listener = None
        self._api_protocol_version_index = None
        self._api_protocol_working = False
        self._api = tinytuya.Device(dev_id, address, local_key)
        self._refresh_task = None
        self._protocol_configured = protocol_version
        self._poll_only = poll_only
        self._temporary_poll = False
        self._reset_cached_state()

        self._hass = hass

        # API calls to update Tuya devices are asynchronous and non-blocking.
        # This means you can send a change and immediately request an updated
        # state (like HA does), but because it has not yet finished processing
        # you will be returned the old state.
        # The solution is to keep a temporary list of changed properties that
        # we can overlay onto the state while we wait for the board to update
        # its switches.
        self._FAKE_IT_TIMEOUT = 5
        self._CACHE_TIMEOUT = 120
        # More attempts are needed in auto mode so we can cycle through all
        # the possibilities a couple of times
        self._AUTO_CONNECTION_ATTEMPTS = len(API_PROTOCOL_VERSIONS) * 2 + 1
        self._SINGLE_PROTO_CONNECTION_ATTEMPTS = 3
        self._lock = Lock()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Return the unique id for this device (the dev_id)."""
        return self._api.id

    @property
    def device_info(self):
        """Return the device information for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Tuya",
        }

    @property
    def has_returned_state(self):
        """Return True if the device has returned some state."""
        return len(self._get_cached_state()) > 1

    def actually_start(self, event=None):
        _LOGGER.debug(f"Starting monitor loop for {self.name}")
        self._running = True
        self._shutdown_listener = self._hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self.async_stop
        )
        self._refresh_task = self._hass.async_create_task(self.receive_loop())

    def start(self):
        if self._hass.is_stopping:
            return
        elif self._hass.is_running:
            if self._startup_listener:
                self._startup_listener()
                self._startup_listener = None
            self.actually_start()
        else:
            self._startup_listener = self._hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.actually_start
            )

    async def async_stop(self, event=None):
        _LOGGER.debug(f"Stopping monitor loop for {self.name}")
        self._running = False
        if self._shutdown_listener:
            self._shutdown_listener()
            self._shutdown_listener = None
        self._children.clear()
        if self._refresh_task:
            await self._refresh_task
        _LOGGER.debug(f"Monitor loop for {self.name} stopped")
        self._refresh_task = None

    def register_entity(self, entity):
        # If this is the first child entity to register, refresh the device
        # state
        should_poll = len(self._children) == 0

        self._children.append(entity)
        if not self._running and not self._startup_listener:
            self.start()
        if self.has_returned_state:
            entity.async_schedule_update_ha_state()
        elif should_poll:
            entity.async_schedule_update_ha_state(True)

    async def async_unregister_entity(self, entity):
        self._children.remove(entity)
        if not self._children:
            await self.async_stop()

    async def receive_loop(self):
        """Coroutine wrapper for async_receive generator."""
        try:
            async for poll in self.async_receive():
                if type(poll) is dict:
                    _LOGGER.debug(f"{self.name} received {poll}")
                    self._cached_state = self._cached_state | poll
                    self._cached_state["updated_at"] = time()
                    for entity in self._children:
                        entity.async_schedule_update_ha_state()
                else:
                    _LOGGER.debug(f"{self.name} received non data {poll}")
            _LOGGER.warning(f"{self.name} receive loop has terminated")

        except Exception as t:
            _LOGGER.exception(
                f"{self.name} receive loop terminated by exception {t}",
            )

    @property
    def should_poll(self):
        return self._poll_only or self._temporary_poll or not self.has_returned_state

    def pause(self):
        self._temporary_poll = True

    def resume(self):
        self._temporary_poll = False

    async def async_receive(self):
        """Receive messages from a persistent connection asynchronously."""
        # If we didn't yet get any state from the device, we may need to
        # negotiate the protocol before making the connection persistent
        persist = not self.should_poll
        self._api.set_socketPersistent(persist)
        while self._running:
            try:
                last_cache = self._cached_state["updated_at"]
                now = time()
                if persist == self.should_poll:
                    # use persistent connections after initial communication
                    # has been established.  Until then, we need to rotate
                    # the protocol version, which seems to require a fresh
                    # connection.
                    persist = not self.should_poll
                    self._api.set_socketPersistent(persist)

                if now - last_cache > self._CACHE_TIMEOUT:
                    poll = await self._retry_on_failed_connection(
                        lambda: self._api.status(),
                        f"Failed to refresh device state for {self.name}",
                    )
                else:
                    await self._hass.async_add_executor_job(
                        self._api.heartbeat,
                        True,
                    )
                    poll = await self._hass.async_add_executor_job(
                        self._api.receive,
                    )

                if poll:
                    if "Error" in poll:
                        _LOGGER.warning(
                            f"{self.name} error reading: {poll['Error']}",
                        )
                        if "Payload" in poll and poll["Payload"]:
                            _LOGGER.info(
                                f"{self.name} err payload: {poll['Payload']}",
                            )
                    else:
                        if "dps" in poll:
                            poll = poll["dps"]
                        yield poll

                await asyncio.sleep(0.1 if self.has_returned_state else 5)

            except asyncio.CancelledError:
                self._running = False
                # Close the persistent connection when exiting the loop
                self._api.set_socketPersistent(False)
                raise
            except Exception as t:
                _LOGGER.exception(
                    f"{self.name} receive loop error {type(t)}:{t}",
                )
                await asyncio.sleep(5)

        # Close the persistent connection when exiting the loop
        self._api.set_socketPersistent(False)

    async def async_possible_types(self):
        cached_state = self._get_cached_state()
        if len(cached_state) <= 1:
            await self.async_refresh()
            cached_state = self._get_cached_state()

        for match in possible_matches(cached_state):
            yield match

    async def async_inferred_type(self):
        best_match = None
        best_quality = 0
        cached_state = {}
        async for config in self.async_possible_types():
            cached_state = self._get_cached_state()
            quality = config.match_quality(cached_state)
            _LOGGER.info(
                f"{self.name} considering {config.name} with quality {quality}"
            )
            if quality > best_quality:
                best_quality = quality
                best_match = config

        if best_match is None:
            _LOGGER.warning(
                f"Detection for {self.name} with dps {cached_state} failed",
            )
            return None

        return best_match.config_type

    async def async_refresh(self):
        _LOGGER.debug(f"Refreshing device state for {self.name}.")
        await self._retry_on_failed_connection(
            lambda: self._refresh_cached_state(),
            f"Failed to refresh device state for {self.name}.",
        )

    def get_property(self, dps_id):
        cached_state = self._get_cached_state()
        if dps_id in cached_state:
            return cached_state[dps_id]
        else:
            return None

    async def async_set_property(self, dps_id, value):
        await self.async_set_properties({dps_id: value})

    def anticipate_property_value(self, dps_id, value):
        """
        Update a value in the cached state only. This is good for when you
        know the device will reflect a new state in the next update, but
        don't want to wait for that update for the device to represent
        this state.

        The anticipated value will be cleared with the next update.
        """
        self._cached_state[dps_id] = value

    def _reset_cached_state(self):
        self._cached_state = {"updated_at": 0}
        self._pending_updates = {}
        self._last_connection = 0

    def _refresh_cached_state(self):
        new_state = self._api.status()
        self._cached_state = self._cached_state | new_state["dps"]
        self._cached_state["updated_at"] = time()
        for entity in self._children:
            entity.async_schedule_update_ha_state()
        _LOGGER.debug(
            f"{self.name} refreshed device state: {json.dumps(new_state, default=non_json)}",
        )
        _LOGGER.debug(
            f"new state (incl pending): {json.dumps(self._get_cached_state(), default=non_json)}"
        )

    async def async_set_properties(self, properties):
        if len(properties) == 0:
            return

        self._add_properties_to_pending_updates(properties)
        await self._debounce_sending_updates()

    def _add_properties_to_pending_updates(self, properties):
        now = time()

        pending_updates = self._get_pending_updates()
        for key, value in properties.items():
            pending_updates[key] = {
                "value": value,
                "updated_at": now,
                "sent": False,
            }

        _LOGGER.debug(
            f"{self.name} new pending updates: {json.dumps(pending_updates, default=non_json)}",
        )

    async def _debounce_sending_updates(self):
        now = time()
        since = now - self._last_connection
        # set this now to avoid a race condition, it will be updated later
        # when the data is actally sent
        self._last_connection = now
        # Only delay a second if there was recently another command.
        # Otherwise delay 1ms, to keep things simple by reusing the
        # same send mechanism.
        waittime = 1 if since < 1.1 else 0.001

        await asyncio.sleep(waittime)
        await self._send_pending_updates()

    async def _send_pending_updates(self):
        pending_properties = self._get_unsent_properties()

        _LOGGER.debug(
            f"{self.name} sending dps update: {json.dumps(pending_properties, default=non_json)}"
        )

        await self._retry_on_failed_connection(
            lambda: self._set_values(pending_properties),
            "Failed to update device state.",
        )

    def _set_values(self, properties):
        try:
            self._lock.acquire()
            self._api.set_multiple_values(properties, nowait=True)
            self._cached_state["updated_at"] = 0
            now = time()
            self._last_connection = now
            pending_updates = self._get_pending_updates()
            for key in properties.keys():
                pending_updates[key]["updated_at"] = now
                pending_updates[key]["sent"] = True
        finally:
            self._lock.release()

    async def _retry_on_failed_connection(self, func, error_message):
        if self._api_protocol_version_index is None:
            await self._rotate_api_protocol_version()
        auto = (self._protocol_configured == "auto") and (
            not self._api_protocol_working
        )
        connections = (
            self._AUTO_CONNECTION_ATTEMPTS
            if auto
            else self._SINGLE_PROTO_CONNECTION_ATTEMPTS
        )

        for i in range(connections):
            try:
                retval = await self._hass.async_add_executor_job(func)
                if type(retval) is dict and "Error" in retval:
                    raise AttributeError
                self._api_protocol_working = True
                return retval
            except Exception as e:
                _LOGGER.debug(
                    f"Retrying after exception {e} ({i}/{connections})",
                )
                if i + 1 == connections:
                    self._reset_cached_state()
                    self._api_protocol_working = False
                    for entity in self._children:
                        entity.async_schedule_update_ha_state()
                    _LOGGER.error(error_message)
                if not self._api_protocol_working:
                    await self._rotate_api_protocol_version()

    def _get_cached_state(self):
        cached_state = self._cached_state.copy()
        return {**cached_state, **self._get_pending_properties()}

    def _get_pending_properties(self):
        return {
            key: property["value"]
            for key, property in self._get_pending_updates().items()
        }

    def _get_unsent_properties(self):
        return {
            key: info["value"]
            for key, info in self._get_pending_updates().items()
            if not info["sent"]
        }

    def _get_pending_updates(self):
        now = time()
        self._pending_updates = {
            key: value
            for key, value in self._pending_updates.items()
            if now - value["updated_at"] < self._FAKE_IT_TIMEOUT
        }
        return self._pending_updates

    async def _rotate_api_protocol_version(self):
        if self._api_protocol_version_index is None:
            try:
                self._api_protocol_version_index = API_PROTOCOL_VERSIONS.index(
                    self._protocol_configured
                )
            except ValueError:
                self._api_protocol_version_index = 0

        # only rotate if configured as auto
        elif self._protocol_configured == "auto":
            self._api_protocol_version_index += 1

        if self._api_protocol_version_index >= len(API_PROTOCOL_VERSIONS):
            self._api_protocol_version_index = 0

        new_version = API_PROTOCOL_VERSIONS[self._api_protocol_version_index]
        _LOGGER.info(
            f"Setting protocol version for {self.name} to {new_version}.",
        )
        await self._hass.async_add_executor_job(
            self._api.set_version,
            new_version,
        )

    @staticmethod
    def get_key_for_value(obj, value, fallback=None):
        keys = list(obj.keys())
        values = list(obj.values())
        return keys[values.index(value)] if value in values else fallback


def setup_device(hass: HomeAssistant, config: dict):
    """Setup a tuya device based on passed in config."""

    _LOGGER.info(f"Creating device: {config[CONF_DEVICE_ID]}")
    hass.data[DOMAIN] = hass.data.get(DOMAIN, {})
    device = TuyaLocalDevice(
        config[CONF_NAME],
        config[CONF_DEVICE_ID],
        config[CONF_HOST],
        config[CONF_LOCAL_KEY],
        config[CONF_PROTOCOL_VERSION],
        hass,
        config[CONF_POLL_ONLY],
    )
    hass.data[DOMAIN][config[CONF_DEVICE_ID]] = {"device": device}

    return device


async def async_delete_device(hass: HomeAssistant, config: dict):
    _LOGGER.info(f"Deleting device: {config[CONF_DEVICE_ID]}")
    await hass.data[DOMAIN][config[CONF_DEVICE_ID]]["device"].async_stop()
    del hass.data[DOMAIN][config[CONF_DEVICE_ID]]["device"]
