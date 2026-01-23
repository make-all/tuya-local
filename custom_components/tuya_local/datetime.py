"""
Setup for Tuya datetime entities
"""

import logging
import time
from datetime import datetime, timedelta, timezone

from homeassistant.components.datetime import DateTimeEntity

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "datetime",
        TuyaLocalDateTime,
    )


class TuyaLocalDateTime(TuyaLocalEntity, DateTimeEntity):
    """Representation of a Tuya DateTime"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the datetime entity.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._year_dps = dps_map.pop("year", None)
        self._month_dps = dps_map.pop("month", None)
        self._day_dps = dps_map.pop("day", None)
        self._hour_dps = dps_map.pop("hour", None)
        self._minute_dps = dps_map.pop("minute", None)
        self._second_dps = dps_map.pop("second", None)
        if (
            self._year_dps is None
            and self._month_dps is None
            and self._day_dps is None
            and self._hour_dps is None
            and self._minute_dps is None
            and self._second_dps is None
        ):
            raise AttributeError(
                f"{config.config_id} is missing an hour, minute or second dp"
            )
        self._init_end(dps_map)

    @property
    def native_value(self):
        """Return the current value of the time."""
        year = month = day = hours = minutes = seconds = None
        tz = timezone.utc
        if self._year_dps:
            year = self._year_dps.get_value(self._device)
            tz = time.now().astimezone().tzinfo
        if self._month_dps:
            month = self._month_dps.get_value(self._device)
        if self._day_dps:
            day = self._day_dps.get_value(self._device)
        if self._hour_dps:
            hours = self._hour_dps.get_value(self._device)
        if self._minute_dps:
            minutes = self._minute_dps.get_value(self._device)
        if self._second_dps:
            seconds = self._second_dps.get_value(self._device)
        if (
            year is None
            and month is None
            and day is None
            and hours is None
            and minutes is None
            and seconds is None
        ):
            return None
        year = year or 1970
        month = month or 1
        day = day or 1
        hours = hours or 0
        minutes = minutes or 0
        seconds = seconds or 0
        delta = timedelta(
            years=int(year) - 1970,
            months=int(month) - 1,
            days=int(day) - 1,
            hours=int(hours),
            minutes=int(minutes),
            seconds=int(seconds),
        )
        return (EPOCH.astimezone(tz) + delta).datetime()

    async def async_set_value(self, value: datetime):
        """Set the datetime."""
        settings = {}
        # Use Local time if split into components
        if self._year_dps:
            tz = time.now().astimezone().tzinfo
            value = value.astimezone(tz)
        year = value.year
        month = value.month
        day = value.day
        hour = value.hour
        minute = value.minute
        second = value.second
        if self._year_dps:
            settings.update(
                self._year_dps.get_values_to_set(self._device, year, settings)
            )
            month = month + (year - 1970) * 12
        if self._month_dps:
            settings.update(
                self._month_dps.get_values_to_set(self._device, month, settings)
            )
        else:
            if self._year_dps is None:
                from_year = 1970
            else:
                from_year = value.year
            day = (
                day
                + (
                    datetime(value.year, value.month, 1) - datetime(from_year, 1, 1)
                ).days
                - 1
            )
        if self._day_dps:
            settings.update(
                self._day_dps.get_values_to_set(self._device, day, settings)
            )
        else:
            hours = hours + day * 24
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
