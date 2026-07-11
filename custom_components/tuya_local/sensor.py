"""
Setup for different kinds of Tuya sensors
"""

import logging
from collections import deque

from homeassistant.components.sensor import (
    STATE_CLASSES,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.helpers.restore_state import RestoreEntity

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity, unit_from_ascii
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("Tuya Local patched sensor.py loaded")

def sensor_factory(device, config):
    """Create the correct sensor implementation."""
    mode = "absolute"
 
    if hasattr(config, "_config") and isinstance(config._config, dict):
        mode = config._config.get("mode", mode)
 
    if mode == "delta":
        return TuyaLocalDeltaSensor(device, config)

    if mode != "absolute":
        _LOGGER.warning(
            "Unsupported sensor mode %s for %s, falling back to absolute",
            mode,
            getattr(config, "name", None),
        )

    return TuyaLocalSensor(device, config)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "sensor",
        sensor_factory,
    )


class TuyaLocalSensor(TuyaLocalEntity, SensorEntity):
    """Representation of a Tuya Sensor"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._sensor_dps = dps_map.pop("sensor", None)
        if self._sensor_dps is None:
            raise AttributeError(f"{config.config_id} is missing a sensor dps")
        self._unit_dps = dps_map.pop("unit", None)

        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class of this device"""
        dclass = self._config.device_class
        if dclass:
            try:
                return SensorDeviceClass(dclass)
            except ValueError:
                _LOGGER.warning(
                    "%s/%s: Unrecognized sensor device class of %s ignored",
                    self._config._device.config,
                    self.name or "sensor",
                    dclass,
                )

    @property
    def state_class(self):
        """Return the state class of this entity"""
        sclass = self._sensor_dps.state_class
        if sclass in STATE_CLASSES:
            return sclass

    @property
    def native_value(self):
        """Return the value reported by the sensor"""
        return self._sensor_dps.get_value(self._device)

    @property
    def native_unit_of_measurement(self):
        """Return the unit for the sensor"""
        if self._unit_dps is None:
            unit = self._sensor_dps.unit
        else:
            unit = self._unit_dps.get_value(self._device)

        return unit_from_ascii(unit)

    @property
    def native_precision(self):
        """Return the precision for the sensor"""
        return self._sensor_dps.precision(self._device)

    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for the sensor"""
        precision = self._sensor_dps.suggested_display_precision
        # if not explicitly defined, get based on scale
        # this is in line with older HA default behavior, and avoids
        # having to override the precision for every scaled sensor.
        if precision is None:
            precision = self._sensor_dps.precision(self._device)

        return precision

    @property
    def options(self):
        """Return a set of possible options."""
        # if mappings are all integers,  they are not options to HA
        values = self._sensor_dps.values(self._device)
        if values:
            for val in values:
                if isinstance(val, str):
                    return values


class TuyaLocalDeltaSensor(TuyaLocalSensor, RestoreEntity):
    """Sensor that handles interval/delta values."""

    def __init__(self, device, config):
        """Initialize the delta sensor."""
        super().__init__(device, config)

        # defaults
        self._delta_function = "total"
        self._averaging_window = 400

        if hasattr(config, "_config") and isinstance(config._config, dict):
            self._delta_function = config._config.get(
                "delta_function",
                self._delta_function,
            )

            if self._delta_function == "average":
                self._averaging_window = int(
                    config._config.get(
                        "averaging_window",
                        self._averaging_window,
                    )
                )
        if self._delta_function not in ("total", "average"):
            _LOGGER.warning(
                "Unsupported delta_function %s for %s, falling back to total",
                self._delta_function,
                getattr(config, "name", None),
            )
            self._delta_function = "total"


        # debug variables
        self._debug_last_logged_start_key = None
        self._debug_last_logged_key = None
        self._debug_last_logged_delta = None

        # for delta_function=total
        self._total = 0.0
        self._counted_for_key = 0.0

        # for delta_function=average
        self._samples = deque()

        # common variables
        self._last_processed_key = None


    async def async_added_to_hass(self):
        """Restore previous total after Home Assistant restart."""
        await super().async_added_to_hass()

        if self._delta_function != "total":
            return

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        try:
            self._total = float(last_state.state)
        except (TypeError, ValueError):
            self._total = 0.0

    def _log_raw_change(self, start_key, key, delta):
        """Log raw delta value changes."""
        if (
            start_key == self._debug_last_logged_start_key
            and key == self._debug_last_logged_key
            and delta == self._debug_last_logged_delta
        ):
            return

        _LOGGER.debug(
            "Raw change: start=%s end=%s delta=%s "
            "prev_start=%s prev_end=%s prev_delta=%s total=%s",
            start_key,
            key,
            delta,
            self._debug_last_logged_start_key,
            self._debug_last_logged_key,
            self._debug_last_logged_delta,
            self._total,
        )

        self._debug_last_logged_start_key = start_key
        self._debug_last_logged_key = key
        self._debug_last_logged_delta = delta

    def _native_total_value(self, key, delta):
        """Return accumulated total from interval deltas."""
        if key != self._last_processed_key:
            self._last_processed_key = key
            self._counted_for_key = 0.0

        if delta > self._counted_for_key:
            self._total += delta - self._counted_for_key
            self._counted_for_key = delta

        return self._total

    def _native_average_value(self, start_key, key, delta, interval_seconds):
        """Return average value over the configured time window."""
        if key != self._last_processed_key:
            self._last_processed_key = key
            self._samples.append(
                (start_key, key, delta, interval_seconds)
            )

        if self._averaging_window > 0:
            self._purge_old_samples(key)
        else:
            while len(self._samples) > 1:
                self._samples.popleft()

        total_delta = sum(sample[2] for sample in self._samples)
        total_seconds = sum(sample[3] for sample in self._samples)

        if total_seconds <= 0:
            return None

        # kWh over seconds -> W
        return round(total_delta * 3600000 / total_seconds, 1)

    def _purge_old_samples(self, newest_key):
        """Remove samples outside the averaging window."""
        cutoff = newest_key - self._averaging_window

        while self._samples and self._samples[0][1] <= cutoff:
            self._samples.popleft()

    @property
    def native_value(self):
        """Return the delta sensor value."""
        start_key = self._get_dp_value("delta_start_key")
        key = self._get_dp_value("delta_key")
        delta = self._get_dp_value("sensor")

        if delta is None or start_key is None or key is None:
            return None

        try:
            delta = float(delta)
            start_key = int(start_key)
            key = int(key)
        except (TypeError, ValueError):
            return None

        interval_seconds = key - start_key
        if interval_seconds <= 0:
            return None

        self._log_raw_change(start_key, key, delta)

        if self._delta_function == "average":
            return self._native_average_value(
                start_key,
                key,
                delta,
                interval_seconds,
            )
        return self._native_total_value(key, delta)

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes or {}
        attrs.update(
            {
                "delta_function": self._delta_function,
                "delta_key": self._last_processed_key,
            }
        )

        if self._delta_function == "total":
            attrs["counted_for_key"] = self._counted_for_key

        if self._delta_function == "average":
            attrs["averaging_window"] = self._averaging_window
            attrs["samples"] = len(self._samples)

        return attrs

    def _get_dp_value(self, name):
        """Get a configured DP value by dps name."""
        dp = self._config.find_dps(name)
        if dp is None:
            return None
        return dp.get_value(self._device)

