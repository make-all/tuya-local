"""
Setup for Tuya time entities
"""

import logging
from datetime import datetime, time, timedelta

from homeassistant.components.time import TimeEntity

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)

MODE_AUTO = "auto"

MIDNIGHT = datetime.combine(datetime.today(), time(0, 0, 0))


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "time",
        TuyaLocalTime,
    )


class TuyaLocalTime(TuyaLocalEntity, TimeEntity):
    """Representation of a Tuya Time"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the time entity.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._hour_dps = dps_map.pop("hour", None)
        self._minute_dps = dps_map.pop("minute", None)
        self._second_dps = dps_map.pop("second", None)
        self._hms_dps = dps_map.pop("hms", None)
        if (
            self._hour_dps is None
            and self._minute_dps is None
            and self._second_dps is None
            and self._hms_dps is None
        ):
            raise AttributeError(
                f"{config.config_id} is missing an hour, minute or second dp"
            )
        self._init_end(dps_map)

    @property
    def native_value(self):
        """Return the current value of the time."""
        hours = minutes = seconds = None
        if self._hour_dps:
            hours = self._hour_dps.get_value(self._device)
        if self._minute_dps:
            minutes = self._minute_dps.get_value(self._device)
        if self._second_dps:
            seconds = self._second_dps.get_value(self._device)
        if self._hms_dps:
            hms = self._hms_dps.get_value(self._device)
            if hms is not None and isinstance(hms, str):
                parts = hms.split(":")
                if len(parts) == 3:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = int(parts[2])
                elif len(parts) == 2:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = 0
                elif len(parts) == 1:
                    if len(hms) <= 2:
                        hours = hms
                    elif len(hms) <= 4:
                        hours = hms[0 : len(hms) - 2]
                        minutes = hms[len(hms) - 2 :]
                    else:
                        hours = hms.substring(0, len(hms) - 4)
                        minutes = hms.substring(len(hms) - 4, len(hms) - 2)
                        seconds = hms.substring(len(hms) - 2)
        if hours is None and minutes is None and seconds is None:
            return None
        hours = hours or 0
        minutes = minutes or 0
        seconds = seconds or 0
        delta = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
        return (MIDNIGHT + delta).time()

    async def async_set_value(self, value: time):
        """Set the number."""
        settings = {}
        hours = value.hour
        minutes = value.minute
        seconds = value.second
        if self._hour_dps:
            settings.update(
                self._hour_dps.get_values_to_set(self._device, hours, settings)
            )
        else:
            minutes = minutes + hours * 60

        if self._minute_dps:
            settings.update(
                self._minute_dps.get_values_to_set(self._device, minutes, settings)
            )
        else:
            seconds = seconds + minutes * 60

        if self._second_dps:
            settings.update(
                self._second_dps.get_values_to_set(self._device, seconds, settings)
            )
        else:
            _LOGGER.debug(
                "%s: Discarding unused precision: %d seconds",
                self.name,
                seconds,
            )

        await self._device.async_set_properties(settings)
