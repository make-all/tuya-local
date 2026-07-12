"""
Active Tuya LAN discovery for configured devices.

When a router hands out new DHCP leases (e.g. after a reboot) a Tuya device
can change IP. The integration then keeps trying the stale ``host`` stored in
the config entry, the device goes unavailable, and the user has to reconfigure
it by hand.

Tuya devices do not all announce themselves unprompted -- in particular
protocol 3.4/3.5 devices stay silent until they receive a discovery request
broadcast to UDP port 7000, at which point they reply with their id (``gwId``),
current IP and ``product_id``. ``tinytuya``'s scanner sends exactly that request,
so ``tinytuya.find_device`` locates a device by its id regardless of how its IP
changed. This is the same mechanism the config flow already uses via
``scan_for_device`` and the one ``localtuya`` uses to find devices in seconds.

This module runs two active-scan tasks for the configured devices:

- a fast sweep (every ``SWEEP_INTERVAL``) that relocates *unreachable* devices:
  it looks up the current IP by device id and updates the config entry's host in
  place. The existing update-listener reload then reconnects the device on the
  new IP -- no manual reconfiguration, no cloud round-trip, history preserved.
  Reachable devices are never scanned, so there is no traffic while healthy.
- a slower scan (every ``SCAN_INTERVAL``) that logs, once per device per HA
  start, when a configured device reports a ``product_id`` that its config file
  does not list under ``products`` -- surfacing devices that may only be
  partially supported so the config can be improved.

References:
- tinytuya scanner discovery request (port 7000 for v3.5 devices):
  https://github.com/jasonacox/tinytuya/blob/master/tinytuya/scanner.py
- the integration's own config-flow scan: config_flow.scan_for_device
"""

import logging
from datetime import timedelta

import tinytuya
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from ..const import CONF_DEVICE_ID, CONF_TYPE, DATA_DISCOVERY, DOMAIN
from .config import get_device_id
from .device_config import get_config

_LOGGER = logging.getLogger(__name__)

# How often to look for unreachable devices. Reachable devices are skipped, so
# a healthy system generates no scan traffic; an unreachable device is normally
# relocated on the first sweep after it drops.
SWEEP_INTERVAL = timedelta(seconds=60)

# How often to scan configured devices to check their product id against the
# config file. Diagnostic only, so it runs infrequently.
SCAN_INTERVAL = timedelta(minutes=10)


def _find_device(device_id):
    """Locate a device by id on the LAN (blocking; run in executor).

    Sends the Tuya discovery request and returns the scanner result dict
    (``{'ip': ..., 'id': ..., 'product_id': ..., ...}``), or a blank result on
    any socket error.
    """
    try:
        return tinytuya.find_device(dev_id=device_id)
    except OSError:
        return {"ip": None}


class TuyaLANRediscovery:
    """Active LAN discovery for configured Tuya devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._unsub_sweep = None
        self._unsub_scan = None
        self._scanning = False
        # device ids already warned about an unmatched product id this run.
        self._warned_products = set()

    @callback
    def async_start(self) -> None:
        """Begin periodic discovery tasks."""
        if self._unsub_sweep is None:
            self._unsub_sweep = async_track_time_interval(
                self._hass, self._async_sweep, SWEEP_INTERVAL
            )
        if self._unsub_scan is None:
            self._unsub_scan = async_track_time_interval(
                self._hass, self._async_product_scan, SCAN_INTERVAL
            )

    @callback
    def async_stop(self, event=None) -> None:
        """Stop periodic discovery tasks."""
        for attr in ("_unsub_sweep", "_unsub_scan"):
            unsub = getattr(self, attr)
            if unsub is not None:
                unsub()
                setattr(self, attr, None)

    def _unreachable_entries(self):
        """Yield (entry, device_id) for configured devices not returning state."""
        domain_data = self._hass.data.get(DOMAIN, {})
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            device_id = entry.data.get(CONF_DEVICE_ID)
            if not device_id:
                continue
            bucket = domain_data.get(get_device_id(entry.data))
            device = bucket.get("device") if bucket else None
            # No device object yet (setup not complete / failed) or it has not
            # returned state recently -> treat as unreachable and worth a scan.
            if device is not None and device.has_returned_state:
                continue
            yield entry, device_id

    async def _async_sweep(self, now=None) -> None:
        """Scan for any unreachable devices and update changed hosts."""
        if self._scanning:
            return
        targets = list(self._unreachable_entries())
        if not targets:
            return

        self._scanning = True
        try:
            for entry, device_id in targets:
                found = await self._hass.async_add_executor_job(_find_device, device_id)
                ip = found.get("ip") if found else None
                if not ip:
                    continue
                current = {**entry.data, **entry.options}.get(CONF_HOST)
                if ip == current:
                    continue
                # WARNING, not INFO: an IP change is a notable operational event
                # the user may want to see, and config entries commonly run at
                # log level WARNING (which would suppress INFO).
                _LOGGER.warning(
                    "%s: LAN IP changed to %s (was %s); updating configuration",
                    entry.title,
                    ip,
                    current,
                )
                # Write the new host wherever it currently takes effect: always
                # to data, and also to options when options carries the host
                # (the options flow stores it there, overriding data), so the
                # merged config actually changes and the entry reloads.
                new_options = entry.options
                if CONF_HOST in entry.options:
                    new_options = {**entry.options, CONF_HOST: ip}
                self._hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_HOST: ip},
                    options=new_options,
                )
        finally:
            self._scanning = False

    async def _async_product_scan(self, now=None) -> None:
        """Warn (once per device per run) about product ids the config lacks."""
        if self._scanning:
            return
        entries = [
            (entry, entry.data.get(CONF_DEVICE_ID), entry.data.get(CONF_TYPE))
            for entry in self._hass.config_entries.async_entries(DOMAIN)
            if entry.data.get(CONF_DEVICE_ID) and entry.data.get(CONF_TYPE)
        ]
        if not entries:
            return

        self._scanning = True
        try:
            for entry, device_id, config_type in entries:
                if device_id in self._warned_products:
                    continue
                found = await self._hass.async_add_executor_job(_find_device, device_id)
                product_id = found.get("product_id") if found else None
                if not product_id:
                    continue
                config = await self._hass.async_add_executor_job(
                    get_config, config_type
                )
                if config is None or config.matches_product(product_id):
                    continue
                # WARNING so it is visible under HA's default log level; once per
                # device per run to avoid noise.
                self._warned_products.add(device_id)
                _LOGGER.warning(
                    "%s: device product id %s is not listed in its config (%s); "
                    "please report it so support can be improved",
                    entry.title,
                    product_id,
                    config_type,
                )
        finally:
            self._scanning = False


async def async_start_discovery(hass: HomeAssistant) -> None:
    """Start the shared LAN discovery service if not already running."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_DISCOVERY) is not None:
        return

    rediscovery = TuyaLANRediscovery(hass)
    domain_data[DATA_DISCOVERY] = rediscovery
    rediscovery.async_start()


@callback
def async_stop_discovery(hass: HomeAssistant) -> None:
    """Stop the shared LAN discovery service if running."""
    domain_data = hass.data.get(DOMAIN, {})
    rediscovery = domain_data.pop(DATA_DISCOVERY, None)
    if rediscovery is not None:
        rediscovery.async_stop()
