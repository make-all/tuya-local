"""
API for Tuya Local devices.
"""

import asyncio
import logging
from threading import Lock
from time import time

import tinytuya
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant

from .const import (
    API_PROTOCOL_VERSIONS,
    CONF_DEVICE_CID,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_POLL_ONLY,
    CONF_PROTOCOL_VERSION,
    DOMAIN,
)
from .helpers.config import get_device_id
from .helpers.device_config import possible_matches
from .helpers.log import log_json

_LOGGER = logging.getLogger(__name__)


class TuyaLocalDevice(object):
    def __init__(
        self,
        name,
        dev_id,
        address,
        local_key,
        protocol_version,
        dev_cid,
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
            dev_cid (str): The sub device id.
            hass (HomeAssistant): The Home Assistant instance.
            poll_only (bool): True if the device should be polled only
        """
        self._name = name
        self._children = []
        self._force_dps = []
        self._running = False
        self._shutdown_listener = None
        self._startup_listener = None
        self._api_protocol_version_index = None
        self._api_protocol_working = False
        self._api_working_protocol_failures = 0
        try:
            if dev_cid:
                self._api = tinytuya.Device(
                    dev_id,
                    cid=dev_cid,
                    parent=tinytuya.Device(dev_id, address, local_key),
                )
            else:
                self._api = tinytuya.Device(dev_id, address, local_key)
            self.dev_cid = dev_cid
        except Exception as e:
            _LOGGER.error(
                "%s: %s while initialising device %s",
                type(e),
                e,
                dev_id,
            )
            raise e

        # we handle retries at a higher level so we can rotate protocol version
        self._api.set_socketRetryLimit(1)
        if self._api.parent:
            self._api.parent.set_socketRetryLimit(1)

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
        self._CACHE_TIMEOUT = 30
        # More attempts are needed in auto mode so we can cycle through all
        # the possibilities a couple of times
        self._AUTO_CONNECTION_ATTEMPTS = len(API_PROTOCOL_VERSIONS) * 2 + 1
        self._SINGLE_PROTO_CONNECTION_ATTEMPTS = 3
        # The number of failures from a working protocol before retrying other protocols.
        self._AUTO_FAILURE_RESET_COUNT = 10
        self._lock = Lock()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Return the unique id for this device (the dev_id or dev_cid)."""
        return self.dev_cid or self._api.id

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
        _LOGGER.debug("Starting monitor loop for %s", self.name)
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
        _LOGGER.debug("Stopping monitor loop for %s", self.name)
        self._running = False
        self._children.clear()
        self._force_dps.clear()
        if self._refresh_task:
            await self._refresh_task
        _LOGGER.debug("Monitor loop for %s stopped", self.name)
        self._refresh_task = None

    def register_entity(self, entity):
        # If this is the first child entity to register, and HA is still
        # starting, refresh the device state so it shows as available without
        # waiting for startup to complete.
        should_poll = len(self._children) == 0 and not self._hass.is_running

        self._children.append(entity)
        for dp in entity._config.dps():
            if dp.force and dp.id not in self._force_dps:
                self._force_dps.append(int(dp.id))

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
                    _LOGGER.debug(
                        "%s received %s",
                        self.name,
                        log_json(poll),
                    )
                    full_poll = poll.pop("full_poll", False)
                    self._cached_state = self._cached_state | poll
                    self._cached_state["updated_at"] = time()
                    self._remove_properties_from_pending_updates(poll)

                    for entity in self._children:
                        # clear non-persistant dps that were not in a full poll
                        if full_poll:
                            for dp in entity._config.dps():
                                if not dp.persist and dp.id not in poll:
                                    self._cached_state.pop(dp.id, None)
                        entity.async_write_ha_state()
                else:
                    _LOGGER.debug(
                        "%s received non data %s",
                        self.name,
                        log_json(poll),
                    )
            _LOGGER.warning("%s receive loop has terminated", self.name)

        except Exception as t:
            _LOGGER.exception(
                "%s receive loop terminated by exception %s", self.name, t
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
        # flag to alternate updatedps and status calls to ensure we get
        # all dps updated
        dps_updated = False

        self._api.set_socketPersistent(persist)
        if self._api.parent:
            self._api.parent.set_socketPersistent(persist)

        while self._running:
            try:
                last_cache = self._cached_state.get("updated_at", 0)
                now = time()
                full_poll = False
                if persist == self.should_poll:
                    # use persistent connections after initial communication
                    # has been established.  Until then, we need to rotate
                    # the protocol version, which seems to require a fresh
                    # connection.
                    persist = not self.should_poll
                    _LOGGER.debug(
                        "%s persistant connection set to %s", self.name, persist
                    )
                    self._api.set_socketPersistent(persist)
                    if self._api.parent:
                        self._api.parent.set_socketPersistent(persist)

                if now - last_cache > self._CACHE_TIMEOUT:
                    if (
                        self._force_dps
                        and not dps_updated
                        and self._api_protocol_working
                    ):
                        poll = await self._retry_on_failed_connection(
                            lambda: self._api.updatedps(self._force_dps),
                            f"Failed to update device dps for {self.name}",
                        )
                        dps_updated = True
                    else:
                        poll = await self._retry_on_failed_connection(
                            lambda: self._api.status(),
                            f"Failed to fetch device status for {self.name}",
                        )
                        dps_updated = False
                        full_poll = True
                elif persist:
                    await self._hass.async_add_executor_job(
                        self._api.heartbeat,
                        True,
                    )
                    poll = await self._hass.async_add_executor_job(
                        self._api.receive,
                    )
                else:
                    await asyncio.sleep(5)
                    poll = None

                if poll:
                    if "Error" in poll:
                        _LOGGER.warning(
                            "%s error reading: %s", self.name, poll["Error"]
                        )
                        if "Payload" in poll and poll["Payload"]:
                            _LOGGER.info(
                                "%s err payload: %s",
                                self.name,
                                poll["Payload"],
                            )
                    else:
                        if "dps" in poll:
                            poll = poll["dps"]
                        poll["full_poll"] = full_poll
                        yield poll

                await asyncio.sleep(0.1 if self.has_returned_state else 5)

            except asyncio.CancelledError:
                self._running = False
                # Close the persistent connection when exiting the loop
                self._api.set_socketPersistent(False)
                if self._api.parent:
                    self._api.parent.set_socketPersistent(False)
                raise
            except Exception as t:
                _LOGGER.exception(
                    "%s receive loop error %s:%s",
                    self.name,
                    type(t),
                    t,
                )
                await asyncio.sleep(5)

        # Close the persistent connection when exiting the loop
        self._api.set_socketPersistent(False)
        if self._api.parent:
            self._api.parent.set_socketPersistent(False)

    async def async_possible_types(self):
        cached_state = self._get_cached_state()
        if len(cached_state) <= 1:
            # in case of device22 devices, we need to poll them with a dp
            # that exists on the device to get anything back.  Most switch-like
            # devices have dp 1. Lights generally start from 20.  101 is where
            # vendor specific dps start.  Between them, these three should cover
            # most devices.  148 covers a doorbell device that didn't have these
            self._api.set_dpsUsed({"1": None, "20": None, "101": None, "148": None})
            await self.async_refresh()
            cached_state = self._get_cached_state()

        for match in possible_matches(cached_state):
            yield match

    async def async_inferred_type(self):
        best_match = None
        best_quality = 0
        cached_state = self._get_cached_state()
        async for config in self.async_possible_types():
            quality = config.match_quality(cached_state)
            _LOGGER.info(
                "%s considering %s with quality %s",
                self.name,
                config.name,
                quality,
            )
            if quality > best_quality:
                best_quality = quality
                best_match = config

        if best_match is None:
            _LOGGER.warning(
                "Detection for %s with dps %s failed",
                self.name,
                log_json(cached_state),
            )
            return None

        return best_match.config_type

    async def async_refresh(self):
        _LOGGER.debug("Refreshing device state for %s", self.name)
        await self._retry_on_failed_connection(
            lambda: self._refresh_cached_state(),
            f"Failed to refresh device state for {self.name}.",
        )

    def get_property(self, dps_id):
        cached_state = self._get_cached_state()
        return cached_state.get(dps_id)

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
        if new_state:
            self._cached_state = self._cached_state | new_state.get("dps", {})
            self._cached_state["updated_at"] = time()
            for entity in self._children:
                for dp in entity._config.dps():
                    # Clear non-persistant dps that were not in the poll
                    if not dp.persist and dp.id not in new_state.get("dps", {}):
                        self._cached_state.pop(dp.id, None)
                entity.async_write_ha_state()
        _LOGGER.debug(
            "%s refreshed device state: %s",
            self.name,
            log_json(new_state),
        )
        _LOGGER.debug(
            "new state (incl pending): %s",
            log_json(self._get_cached_state()),
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
            "%s new pending updates: %s",
            self.name,
            log_json(pending_updates),
        )

    def _remove_properties_from_pending_updates(self, data):
        self._pending_updates = {
            key: value
            for key, value in self._pending_updates.items()
            if key not in data or not value["sent"] or data[key] != value["value"]
        }

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
            "%s sending dps update: %s",
            self.name,
            log_json(pending_properties),
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
                if not self._hass.is_stopping:
                    retval = await self._hass.async_add_executor_job(func)
                    if type(retval) is dict and "Error" in retval:
                        raise AttributeError(retval["Error"])
                    self._api_protocol_working = True
                    self._api_working_protocol_failures = 0
                    return retval
            except Exception as e:
                _LOGGER.debug(
                    "Retrying after exception %s %s (%d/%d)",
                    type(e),
                    e,
                    i,
                    connections,
                )

                if i + 1 == connections:
                    self._reset_cached_state()
                    self._api_working_protocol_failures += 1
                    if (
                        self._api_working_protocol_failures
                        > self._AUTO_FAILURE_RESET_COUNT
                    ):
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
        # sort pending updates according to their API identifier
        pending_updates_sorted = sorted(
            self._pending_updates.items(), key=lambda x: int(x[0])
        )
        self._pending_updates = {
            key: value
            for key, value in pending_updates_sorted
            if not value["sent"]
            or now - value.get("updated_at", 0) < self._FAKE_IT_TIMEOUT
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
            "Setting protocol version for %s to %0.1f",
            self.name,
            new_version,
        )
        await self._hass.async_add_executor_job(
            self._api.set_version,
            new_version,
        )
        if self._api.parent:
            await self._hass.async_add_executor_job(
                self._api.parent.set_version,
                new_version,
            )

    @staticmethod
    def get_key_for_value(obj, value, fallback=None):
        keys = list(obj.keys())
        values = list(obj.values())
        return keys[values.index(value)] if value in values else fallback


def setup_device(hass: HomeAssistant, config: dict):
    """Setup a tuya device based on passed in config."""

    _LOGGER.info("Creating device: %s", get_device_id(config))
    hass.data[DOMAIN] = hass.data.get(DOMAIN, {})
    device = TuyaLocalDevice(
        config[CONF_NAME],
        config[CONF_DEVICE_ID],
        config[CONF_HOST],
        config[CONF_LOCAL_KEY],
        config[CONF_PROTOCOL_VERSION],
        config.get(CONF_DEVICE_CID),
        hass,
        config[CONF_POLL_ONLY],
    )
    hass.data[DOMAIN][get_device_id(config)] = {"device": device}

    return device


async def async_delete_device(hass: HomeAssistant, config: dict):
    device_id = get_device_id(config)
    _LOGGER.info("Deleting device: %s", device_id)
    await hass.data[DOMAIN][device_id]["device"].async_stop()
    del hass.data[DOMAIN][device_id]["device"]
