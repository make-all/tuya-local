"""Tests for the cover entity."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.cover import TuyaLocalCover, async_setup_entry


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "garage_door_opener",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {
            "device": m_device,
        },
    }
    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["cover_garage"]) is TuyaLocalCover
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_cover(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "kogan_heater",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {
        "dummy": {
            "device": m_device,
        },
    }
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_init_entry_fails_if_config_is_missing(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "non_existing",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


def _make_cover(
    position=True,
    currentpos=False,
    tiltpos=False,
    control=True,
    action=True,
    open_dp=False,
    control_values=None,
):
    """Create a TuyaLocalCover with mocked internals."""
    if control_values is None:
        control_values = ["open", "close", "stop"]

    device = MagicMock()
    config = MagicMock()
    config.device_class = None
    config.name = "Test Cover"
    config.translation_key = None
    config.translation_only_key = None
    config.translation_placeholders = None
    config.entity_category = None

    dps = {}
    if position:
        dp = MagicMock()
        dp.name = "position"
        dps["position"] = dp
    if currentpos:
        dp = MagicMock()
        dp.name = "current_position"
        dps["current_position"] = dp
    if tiltpos:
        dp = MagicMock()
        dp.name = "tilt_position"
        dps["tilt_position"] = dp
    if control:
        dp = MagicMock()
        dp.name = "control"
        dp.values.return_value = control_values
        dps["control"] = dp
    if action:
        dp = MagicMock()
        dp.name = "action"
        dps["action"] = dp
    if open_dp:
        dp = MagicMock()
        dp.name = "open"
        dps["open"] = dp

    config.dps.return_value = list(dps.values())

    # Patch __init__ to avoid MRO issues with HA entity base classes
    cover = object.__new__(TuyaLocalCover)
    cover._device = device
    cover._config = config
    cover._attr_dps = []
    cover._attr_translation_key = None
    cover._attr_translation_placeholders = None

    cover._position_dp = dps.get("position")
    cover._currentpos_dp = dps.get("current_position")
    cover._tiltpos_dp = dps.get("tilt_position")
    cover._control_dp = dps.get("control")
    cover._action_dp = dps.get("action")
    cover._open_dp = dps.get("open")

    # Build support flags
    cover._support_flags = CoverEntityFeature(0)
    if cover._position_dp:
        cover._support_flags |= CoverEntityFeature.SET_POSITION
    if cover._control_dp:
        vals = cover._control_dp.values(device)
        if "stop" in vals:
            cover._support_flags |= CoverEntityFeature.STOP
        if "open" in vals:
            cover._support_flags |= CoverEntityFeature.OPEN
        if "close" in vals:
            cover._support_flags |= CoverEntityFeature.CLOSE
    if cover._tiltpos_dp:
        cover._support_flags |= CoverEntityFeature.SET_TILT_POSITION

    return cover


class TestSupportedFeatures:
    def test_all_features(self):
        cover = _make_cover(position=True, control=True, tiltpos=True)
        flags = cover.supported_features
        assert flags & CoverEntityFeature.SET_POSITION
        assert flags & CoverEntityFeature.STOP
        assert flags & CoverEntityFeature.OPEN
        assert flags & CoverEntityFeature.CLOSE
        assert flags & CoverEntityFeature.SET_TILT_POSITION

    def test_position_only(self):
        cover = _make_cover(position=True, control=False, tiltpos=False, action=False)
        flags = cover.supported_features
        assert flags & CoverEntityFeature.SET_POSITION
        assert not (flags & CoverEntityFeature.STOP)

    def test_no_stop(self):
        cover = _make_cover(control=True, control_values=["open", "close"])
        flags = cover.supported_features
        assert not (flags & CoverEntityFeature.STOP)
        assert flags & CoverEntityFeature.OPEN
        assert flags & CoverEntityFeature.CLOSE


class TestDeviceClass:
    def test_valid_class(self):
        cover = _make_cover()
        cover._config.device_class = "garage"
        assert cover.device_class == CoverDeviceClass.GARAGE

    def test_none_class(self):
        cover = _make_cover()
        cover._config.device_class = None
        assert cover.device_class is None

    def test_invalid_class_logs_warning(self):
        cover = _make_cover()
        cover._config.device_class = "invalid_class"
        with patch("custom_components.tuya_local.cover._LOGGER") as mock_logger:
            result = cover.device_class
            assert result is None
            mock_logger.warning.assert_called_once()


class TestStateToPercent:
    def test_opened(self):
        cover = _make_cover()
        assert cover._state_to_percent("opened") == 100

    def test_closed(self):
        cover = _make_cover()
        assert cover._state_to_percent("closed") == 0

    def test_other(self):
        cover = _make_cover()
        assert cover._state_to_percent("opening") == 50


class TestCurrentCoverPosition:
    def test_from_currentpos_dp(self):
        cover = _make_cover(currentpos=True)
        cover._currentpos_dp.get_value.return_value = 75
        assert cover.current_cover_position == 75

    def test_currentpos_none_falls_through(self):
        cover = _make_cover(currentpos=True, action=True)
        cover._currentpos_dp.get_value.return_value = None
        cover._action_dp.get_value.return_value = "opened"
        assert cover.current_cover_position == 100

    def test_from_open_dp_true(self):
        cover = _make_cover(
            currentpos=False, open_dp=True, action=False, control=False, position=False
        )
        cover._open_dp.get_value.return_value = True
        assert cover.current_cover_position == 100

    def test_from_open_dp_false(self):
        cover = _make_cover(
            currentpos=False, open_dp=True, action=False, control=False, position=False
        )
        cover._open_dp.get_value.return_value = False
        assert cover.current_cover_position == 0

    def test_from_action_dp(self):
        cover = _make_cover(
            currentpos=False, open_dp=False, action=True, control=False, position=False
        )
        cover._action_dp.get_value.return_value = "closed"
        assert cover.current_cover_position == 0

    def test_from_position_dp(self):
        cover = _make_cover(
            currentpos=False, open_dp=False, action=False, control=False, position=True
        )
        cover._position_dp.get_value.return_value = 42
        assert cover.current_cover_position == 42

    def test_none_when_no_dps(self):
        cover = _make_cover(
            currentpos=False,
            open_dp=False,
            action=False,
            control=False,
            position=False,
        )
        assert cover.current_cover_position is None


class TestCurrentCoverTiltPosition:
    def test_with_range(self):
        cover = _make_cover(tiltpos=True)
        cover._tiltpos_dp.range.return_value = (0, 255)
        cover._tiltpos_dp.get_value.return_value = 128
        pos = cover.current_cover_tilt_position
        assert pos is not None
        assert 0 <= pos <= 100

    def test_without_range(self):
        cover = _make_cover(tiltpos=True)
        cover._tiltpos_dp.range.return_value = None
        cover._tiltpos_dp.get_value.return_value = 50
        assert cover.current_cover_tilt_position == 50

    def test_none_without_dp(self):
        cover = _make_cover(tiltpos=False)
        assert cover.current_cover_tilt_position is None


class TestCurrentState:
    def test_action_opening(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "opening"
        assert cover._current_state == "opening"

    def test_action_closing(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "closing"
        assert cover._current_state == "closing"

    def test_action_opened(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "opened"
        assert cover._current_state == "opened"

    def test_action_closed(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "closed"
        assert cover._current_state == "closed"

    def test_action_unknown_falls_to_position(self):
        cover = _make_cover(currentpos=True, action=True)
        cover._action_dp.get_value.return_value = "idle"
        cover._currentpos_dp.get_value.return_value = 0
        assert cover._current_state == "closed"

    def test_position_low_is_closed(self):
        cover = _make_cover(action=False, currentpos=True)
        cover._currentpos_dp.get_value.return_value = 3
        assert cover._current_state == "closed"

    def test_position_high_is_opened(self):
        cover = _make_cover(action=False, currentpos=True)
        cover._currentpos_dp.get_value.return_value = 98
        assert cover._current_state == "opened"

    def test_mid_position_with_setpos_match_is_opened(self):
        cover = _make_cover(action=False, currentpos=True, position=True)
        cover._currentpos_dp.get_value.return_value = 50
        cover._position_dp.get_value.return_value = 50
        assert cover._current_state == "opened"

    def test_mid_position_near_setpos_is_opened(self):
        cover = _make_cover(action=False, currentpos=True, position=True)
        cover._currentpos_dp.get_value.return_value = 49
        cover._position_dp.get_value.return_value = 50
        assert cover._current_state == "opened"

    def test_mid_position_with_open_cmd_is_opening(self):
        cover = _make_cover(action=False, currentpos=True, position=True, control=True)
        cover._currentpos_dp.get_value.return_value = 50
        cover._position_dp.get_value.return_value = 80
        cover._control_dp.get_value.return_value = "open"
        assert cover._current_state == "opening"

    def test_mid_position_with_close_cmd_is_closing(self):
        cover = _make_cover(action=False, currentpos=True, position=True, control=True)
        cover._currentpos_dp.get_value.return_value = 50
        cover._position_dp.get_value.return_value = 20
        cover._control_dp.get_value.return_value = "close"
        assert cover._current_state == "closing"

    def test_none_when_no_position(self):
        cover = _make_cover(
            action=False,
            currentpos=False,
            position=False,
            control=False,
            open_dp=False,
        )
        assert cover._current_state is None


class TestIsOpeningClosingClosed:
    def test_is_opening_true(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "opening"
        assert cover.is_opening is True

    def test_is_opening_false(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "closed"
        assert cover.is_opening is False

    def test_is_opening_none(self):
        cover = _make_cover(
            action=False,
            currentpos=False,
            position=False,
            control=False,
            open_dp=False,
        )
        assert cover.is_opening is None

    def test_is_closing_true(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "closing"
        assert cover.is_closing is True

    def test_is_closing_false(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "opened"
        assert cover.is_closing is False

    def test_is_closing_none(self):
        cover = _make_cover(
            action=False,
            currentpos=False,
            position=False,
            control=False,
            open_dp=False,
        )
        assert cover.is_closing is None

    def test_is_closed_true(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "closed"
        assert cover.is_closed is True

    def test_is_closed_false(self):
        cover = _make_cover()
        cover._action_dp.get_value.return_value = "opened"
        assert cover.is_closed is False

    def test_is_closed_none(self):
        cover = _make_cover(
            action=False,
            currentpos=False,
            position=False,
            control=False,
            open_dp=False,
        )
        assert cover.is_closed is None


class TestAsyncOpenCover:
    @pytest.mark.asyncio
    async def test_open_with_control(self):
        cover = _make_cover()
        cover._control_dp.async_set_value = AsyncMock()
        await cover.async_open_cover()
        cover._control_dp.async_set_value.assert_awaited_once_with(
            cover._device, "open"
        )

    @pytest.mark.asyncio
    async def test_open_with_position(self):
        cover = _make_cover(control=False)
        cover._position_dp.async_set_value = AsyncMock()
        await cover.async_open_cover()
        cover._position_dp.async_set_value.assert_awaited_once_with(cover._device, 100)

    @pytest.mark.asyncio
    async def test_open_raises_not_implemented(self):
        cover = _make_cover(control=False, position=False, action=False)
        with pytest.raises(NotImplementedError):
            await cover.async_open_cover()


class TestAsyncCloseCover:
    @pytest.mark.asyncio
    async def test_close_with_control(self):
        cover = _make_cover()
        cover._control_dp.async_set_value = AsyncMock()
        await cover.async_close_cover()
        cover._control_dp.async_set_value.assert_awaited_once_with(
            cover._device, "close"
        )

    @pytest.mark.asyncio
    async def test_close_with_position(self):
        cover = _make_cover(control=False)
        cover._position_dp.async_set_value = AsyncMock()
        await cover.async_close_cover()
        cover._position_dp.async_set_value.assert_awaited_once_with(cover._device, 0)

    @pytest.mark.asyncio
    async def test_close_raises_not_implemented(self):
        cover = _make_cover(control=False, position=False, action=False)
        with pytest.raises(NotImplementedError):
            await cover.async_close_cover()


class TestAsyncSetCoverPosition:
    @pytest.mark.asyncio
    async def test_set_position(self):
        cover = _make_cover()
        cover._position_dp.async_set_value = AsyncMock()
        await cover.async_set_cover_position(position=50)
        cover._position_dp.async_set_value.assert_awaited_once_with(cover._device, 50)

    @pytest.mark.asyncio
    async def test_set_position_none_raises(self):
        cover = _make_cover()
        with pytest.raises(AttributeError):
            await cover.async_set_cover_position(position=None)

    @pytest.mark.asyncio
    async def test_set_position_no_dp_raises(self):
        cover = _make_cover(position=False, action=False)
        with pytest.raises(NotImplementedError):
            await cover.async_set_cover_position(position=50)


class TestAsyncSetCoverTiltPosition:
    @pytest.mark.asyncio
    async def test_tilt_with_fixed_values(self):
        cover = _make_cover(tiltpos=True)
        cover._tiltpos_dp.values.return_value = [0, 50, 100]
        cover._tiltpos_dp.range.return_value = None
        cover._tiltpos_dp.async_set_value = AsyncMock()
        await cover.async_set_cover_tilt_position(tilt_position=60)
        # Should snap to 50 (closest)
        cover._tiltpos_dp.async_set_value.assert_awaited_once_with(cover._device, 50)

    @pytest.mark.asyncio
    async def test_tilt_with_range(self):
        cover = _make_cover(tiltpos=True)
        cover._tiltpos_dp.values.return_value = []
        cover._tiltpos_dp.range.return_value = (0, 255)
        cover._tiltpos_dp.async_set_value = AsyncMock()
        await cover.async_set_cover_tilt_position(tilt_position=50)
        cover._tiltpos_dp.async_set_value.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_tilt_raw(self):
        cover = _make_cover(tiltpos=True)
        cover._tiltpos_dp.values.return_value = []
        cover._tiltpos_dp.range.return_value = None
        cover._tiltpos_dp.async_set_value = AsyncMock()
        await cover.async_set_cover_tilt_position(tilt_position=75)
        cover._tiltpos_dp.async_set_value.assert_awaited_once_with(cover._device, 75)

    @pytest.mark.asyncio
    async def test_tilt_no_dp_raises(self):
        cover = _make_cover(tiltpos=False)
        with pytest.raises(NotImplementedError):
            await cover.async_set_cover_tilt_position(tilt_position=50)


class TestAsyncStopCover:
    @pytest.mark.asyncio
    async def test_stop_with_control(self):
        cover = _make_cover()
        cover._control_dp.async_set_value = AsyncMock()
        await cover.async_stop_cover()
        cover._control_dp.async_set_value.assert_awaited_once_with(
            cover._device, "stop"
        )

    @pytest.mark.asyncio
    async def test_stop_raises_not_implemented(self):
        cover = _make_cover(control=False, position=False, action=False)
        with pytest.raises(NotImplementedError):
            await cover.async_stop_cover()
