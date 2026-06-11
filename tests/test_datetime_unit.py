"""Unit tests for the TuyaLocalDateTime class."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.tuya_local.datetime import TuyaLocalDateTime


def _make_dp(name, value=None):
    dp = MagicMock()
    dp.name = name
    dp.hidden = False
    dp.optional = True
    dp.get_value.return_value = value
    dp.get_values_to_set.side_effect = lambda dev, val, s: {name: val}
    return dp


def _make_datetime(
    year=None,
    month=None,
    day=None,
    hour=None,
    minute=None,
    second=None,
):
    """Create a TuyaLocalDateTime with mocked internals."""
    device = MagicMock()
    config = MagicMock()
    config.name = "Test DateTime"
    config.translation_key = None
    config.translation_only_key = None
    config.translation_placeholders = None
    config.entity_category = None
    config.config_id = "test_datetime"

    dps = {}
    dp_list = []
    if year is not None:
        dp = _make_dp("year", year)
        dps["year"] = dp
        dp_list.append(dp)
    if month is not None:
        dp = _make_dp("month", month)
        dps["month"] = dp
        dp_list.append(dp)
    if day is not None:
        dp = _make_dp("day", day)
        dps["day"] = dp
        dp_list.append(dp)
    if hour is not None:
        dp = _make_dp("hour", hour)
        dps["hour"] = dp
        dp_list.append(dp)
    if minute is not None:
        dp = _make_dp("minute", minute)
        dps["minute"] = dp
        dp_list.append(dp)
    if second is not None:
        dp = _make_dp("second", second)
        dps["second"] = dp
        dp_list.append(dp)

    config.dps.return_value = dp_list

    entity = object.__new__(TuyaLocalDateTime)
    entity._device = device
    entity._config = config
    entity._attr_dps = []
    entity._attr_translation_key = None
    entity._attr_translation_placeholders = None
    entity._year_dps = dps.get("year")
    entity._month_dps = dps.get("month")
    entity._day_dps = dps.get("day")
    entity._hour_dps = dps.get("hour")
    entity._minute_dps = dps.get("minute")
    entity._second_dps = dps.get("second")

    return entity


class TestNativeValue:
    def test_all_none_returns_none(self):
        # Create with dps present but returning None values
        entity = _make_datetime(hour=0, minute=0, second=0)
        entity._hour_dps.get_value.return_value = None
        entity._minute_dps.get_value.return_value = None
        entity._second_dps.get_value.return_value = None
        assert entity.native_value is None

    def test_hour_minute_second(self):
        entity = _make_datetime(hour=10, minute=30, second=45)
        result = entity.native_value
        assert result is not None
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_hour_only(self):
        entity = _make_datetime(hour=14)
        result = entity.native_value
        assert result is not None
        assert result.hour == 14
        assert result.minute == 0
        assert result.second == 0

    def test_minute_only(self):
        entity = _make_datetime(minute=45)
        result = entity.native_value
        assert result is not None
        assert result.minute == 45

    def test_defaults_when_partial(self):
        entity = _make_datetime(hour=5, minute=0, second=0)
        result = entity.native_value
        assert result.year == 1970
        assert result.month == 1


class TestAsyncSetValue:
    @pytest.mark.asyncio
    async def test_set_hour_minute_second(self):
        entity = _make_datetime(hour=0, minute=0, second=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 1, 1, 14, 30, 45, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        entity._device.async_set_properties.assert_awaited_once()
        settings = entity._device.async_set_properties.call_args[0][0]
        assert settings["hour"] == 14
        assert settings["minute"] == 30
        assert settings["second"] == 45

    @pytest.mark.asyncio
    async def test_set_without_second_dp(self):
        entity = _make_datetime(hour=0, minute=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 1, 1, 10, 20, 30, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        settings = entity._device.async_set_properties.call_args[0][0]
        assert settings["hour"] == 10
        assert settings["minute"] == 20
        assert "second" not in settings

    @pytest.mark.asyncio
    async def test_set_without_hour_dp(self):
        entity = _make_datetime(minute=0, second=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 1, 1, 2, 30, 15, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        settings = entity._device.async_set_properties.call_args[0][0]
        # hour=2 should be folded into minutes: 2*60 + 30 = 150
        assert settings["minute"] == 150
        assert settings["second"] == 15

    @pytest.mark.asyncio
    async def test_set_without_minute_dp(self):
        entity = _make_datetime(hour=0, second=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 1, 1, 1, 5, 30, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        settings = entity._device.async_set_properties.call_args[0][0]
        assert settings["hour"] == 1
        # minute=5 folded into seconds: 5*60 + 30 = 330
        assert settings["second"] == 330

    @pytest.mark.asyncio
    async def test_set_without_day_dp(self):
        entity = _make_datetime(hour=0, minute=0, second=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 1, 2, 3, 0, 0, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        settings = entity._device.async_set_properties.call_args[0][0]
        # day=2 (1 extra day) should fold into hours: 1*24 + 3 = 27
        assert settings["hour"] == 27

    @pytest.mark.asyncio
    async def test_set_with_day_dp(self):
        entity = _make_datetime(day=0, hour=0, minute=0, second=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 1, 15, 8, 30, 0, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        settings = entity._device.async_set_properties.call_args[0][0]
        assert settings["hour"] == 8
        assert settings["minute"] == 30

    @pytest.mark.asyncio
    async def test_set_with_month_dp(self):
        entity = _make_datetime(month=0, day=0, hour=0, minute=0, second=0)
        entity._device.async_set_properties = AsyncMock()
        value = datetime(1970, 3, 5, 12, 0, 0, tzinfo=timezone.utc)
        await entity.async_set_value(value)
        settings = entity._device.async_set_properties.call_args[0][0]
        assert settings["month"] == 3
        assert settings["hour"] == 12
