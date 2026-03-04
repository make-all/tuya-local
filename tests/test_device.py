from time import time

import pytest

# from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from custom_components.tuya_local.device import TuyaLocalDevice

from .const import EUROM_600_HEATER_PAYLOAD


@pytest.fixture
def mock_api(mocker):
    mock = mocker.patch("tinytuya.Device")
    mock.parent = None
    yield mock


@pytest.fixture
def patched_hass(hass, mocker):
    hass.is_running = True
    hass.is_stopping = False
    hass.data = {"tuya_local": {}}

    async def job(func, *args):
        print(f"{args}")
        return func(*args)

    mocker.patch.object(hass, "async_add_executor_job", side_effect=job)
    mocker.patch.object(hass, "async_create_task")
    return hass


@pytest.fixture
def subject(patched_hass, mock_api, mocker):
    subject = TuyaLocalDevice(
        "Some name",
        "some_dev_id",
        "some.ip.address",
        "some_local_key",
        "auto",
        None,
        patched_hass,
    )
    # For most tests we want the protocol working
    subject._api_protocol_version_index = 0
    subject._api_protocol_working = True
    subject._protocol_configured = "auto"
    return subject


def test_name(subject):
    """Returns the name given at instantiation."""
    assert subject.name == "Some name"


def test_unique_id(subject, mock_api):
    """Returns the unique ID presented by the API class."""
    assert subject.unique_id is mock_api().id


def test_device_info(subject, mock_api):
    """Returns generic info plus the unique ID for categorisation."""
    assert subject.device_info == {
        "identifiers": {("tuya_local", mock_api().id)},
        "name": "Some name",
        "manufacturer": "Tuya",
    }


def test_has_returned_state(subject):
    """Returns True if the device has returned its state."""
    subject._cached_state = EUROM_600_HEATER_PAYLOAD
    assert subject.has_returned_state

    subject._cached_state = {"updated_at": 0}
    assert not subject.has_returned_state


@pytest.mark.asyncio
async def test_refreshes_state_if_no_cached_state_exists(subject, mocker):
    subject._cached_state = {}
    subject.async_refresh = mocker.AsyncMock()

    await subject.async_inferred_type()

    subject.async_refresh.assert_awaited()


@pytest.mark.asyncio
async def test_detection_returns_none_when_device_type_not_detected(subject):
    subject._cached_state = {"192": False, "updated_at": time()}
    assert await subject.async_inferred_type() is None


@pytest.mark.asyncio
async def test_refresh_retries_up_to_eleven_times(subject, mock_api):
    subject._api_protocol_working = False
    mock_api().status.side_effect = [
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        {"dps": {"1": False}},
    ]

    await subject.async_refresh()

    assert mock_api().status.call_count == 11
    assert subject._cached_state["1"] is False


@pytest.mark.asyncio
async def test_refresh_clears_cache_after_allowed_failures(subject, mock_api):
    subject._cached_state = {"1": True}
    subject._pending_updates = {
        "1": {"value": False, "updated_at": time(), "sent": True}
    }
    mock_api().status.side_effect = [
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
    ]

    await subject.async_refresh()

    assert mock_api().status.call_count == 3
    assert subject._cached_state == {"updated_at": 0}
    assert subject._pending_updates == {}


@pytest.mark.asyncio
async def test_api_protocol_version_is_rotated_with_each_failure(
    subject, mock_api, mocker
):
    subject._api_protocol_version_index = None
    subject._api_protocol_working = False
    mock_api().status.side_effect = [
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
    ]
    await subject.async_refresh()

    mock_api().set_version.assert_has_calls(
        [
            mocker.call(3.1),
            mocker.call(3.2),
            mocker.call(3.4),
            mocker.call(3.5),
            mocker.call(3.3),
            mocker.call(3.3),
            mocker.call(3.1),
        ]
    )


@pytest.mark.asyncio
async def test_api_protocol_version_is_stable_once_successful(
    subject, mock_api, mocker
):
    subject._api_protocol_version_index = None
    subject._api_protocol_working = False
    mock_api().status.side_effect = [
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        {"dps": {"1": False}},
        {"dps": {"1": False}},
        Exception("Error"),
        Exception("Error"),
        {"dps": {"1": False}},
    ]

    await subject.async_refresh()
    assert subject._api_protocol_version_index == 3
    assert subject._api_protocol_working
    await subject.async_refresh()
    assert subject._api_protocol_version_index == 3
    await subject.async_refresh()
    assert subject._api_protocol_version_index == 3

    mock_api().set_version.assert_has_calls(
        [
            mocker.call(3.1),
            mocker.call(3.2),
            mocker.call(3.4),
        ]
    )


@pytest.mark.asyncio
async def test_api_protocol_version_is_not_rotated_when_not_auto(subject, mock_api):
    # Set up preconditions for the test

    subject._protocol_configured = 3.4
    subject._api_protocol_version_index = None
    subject._api_protocol_working = False
    mock_api().status.side_effect = [
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        {"dps": {"1": False}},
        {"dps": {"1": False}},
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        Exception("Error"),
        {"dps": {"1": False}},
    ]
    await subject._rotate_api_protocol_version()
    mock_api().set_version.assert_called_once_with(3.4)
    mock_api().set_version.reset_mock()

    await subject.async_refresh()
    assert subject._api_protocol_version_index == 3
    await subject.async_refresh()
    assert subject._api_protocol_version_index == 3
    await subject.async_refresh()
    assert subject._api_protocol_version_index == 3


def test_reset_cached_state_clears_cached_state_and_pending_updates(subject):
    subject._cached_state = {"1": True, "updated_at": time()}
    subject._pending_updates = {
        "1": {"value": False, "updated_at": time(), "sent": True}
    }

    subject._reset_cached_state()

    assert subject._cached_state == {"updated_at": 0}
    assert subject._pending_updates == {}


def test_get_property_returns_value_from_cached_state(subject):
    subject._cached_state = {"1": True}
    assert subject.get_property("1") is True


def test_get_property_returns_pending_update_value(subject):
    subject._pending_updates = {
        "1": {"value": False, "updated_at": time() - 4, "sent": True}
    }
    assert subject.get_property("1") is False


def test_pending_update_value_overrides_cached_value(subject):
    subject._cached_state = {"1": True}
    subject._pending_updates = {
        "1": {"value": False, "updated_at": time() - 4, "sent": True}
    }

    assert subject.get_property("1") is False


def test_expired_pending_update_value_does_not_override_cached_value(subject):
    subject._cached_state = {"1": True}
    subject._pending_updates = {
        "1": {"value": False, "updated_at": time() - 5, "sent": True}
    }

    assert subject.get_property("1") is True


def test_get_property_returns_none_when_value_does_not_exist(subject):
    subject._cached_state = {"1": True}
    assert subject.get_property("2") is None


@pytest.mark.asyncio
async def test_async_set_property_sends_to_api(subject, mock_api):
    await subject.async_set_property("1", False)

    mock_api().set_multiple_values.assert_called_once()


@pytest.mark.asyncio
async def test_set_property_immediately_stores_pending_updates(subject):
    subject._cached_state = {"1": True}
    await subject.async_set_property("1", False)
    assert not subject.get_property("1")


@pytest.mark.asyncio
async def test_set_properties_takes_no_action_when_nothing_provided(subject, mocker):
    mock = mocker.patch("asyncio.sleep")
    await subject.async_set_properties({})
    mock.assert_not_called()


def test_anticipate_property_value_updates_cached_state(subject):
    subject._cached_state = {"1": True}
    subject.anticipate_property_value("1", False)
    assert subject._cached_state["1"] is False


def test_get_key_for_value_returns_key_from_object_matching_value(subject):
    obj = {"key1": "value1", "key2": "value2"}

    assert TuyaLocalDevice.get_key_for_value(obj, "value1") == "key1"
    assert TuyaLocalDevice.get_key_for_value(obj, "value2") == "key2"


def test_get_key_for_value_returns_fallback_when_value_not_found(subject):
    obj = {"key1": "value1", "key2": "value2"}
    assert TuyaLocalDevice.get_key_for_value(obj, "value3", fallback="fb") == "fb"


def test_refresh_cached_state(subject, mock_api):
    # set up preconditions
    mock_api().status.return_value = {"dps": {"1": "CHANGED"}}
    subject._cached_state = {"1": "UNCHANGED", "updated_at": 123}

    # call the function under test
    subject._refresh_cached_state()

    # Did it call the API as expected?
    mock_api().status.assert_called_once()
    # Did it update the cached state?
    assert subject._cached_state == {"1": "CHANGED"} | subject._cached_state
    # Did it update the timestamp on the cached state?
    assert subject._cached_state["updated_at"] == pytest.approx(time(), abs=2)


def test_set_values(subject, mock_api):
    # set up preconditions
    subject._pending_updates = {
        "1": {"value": "sample", "updated_at": time() - 2, "sent": False},
    }

    # call the function under test
    subject._set_values({"1": "sample"})

    # did it send what it was asked?
    mock_api().set_multiple_values.assert_called_once_with({"1": "sample"}, nowait=True)
    # did it mark the pending updates as sent?
    assert subject._pending_updates["1"]["sent"]
    # did it update the time on the pending updates?
    assert subject._pending_updates["1"]["updated_at"] == pytest.approx(time(), abs=2)
    # did it lock and unlock when sending
    # subject._lock.acquire.assert_called_once()
    # subject._lock.release.assert_called_once()


def test_pending_updates_cleared_on_receipt(subject):
    # Set up the preconditions
    now = time()
    subject._pending_updates = {
        "1": {"value": True, "updated_at": now, "sent": True},
        "2": {"value": True, "updated_at": now, "sent": False},  # unsent
        "3": {"value": True, "updated_at": now, "sent": True},  # unmatched
        "4": {"value": True, "updated_at": now, "sent": True},  # not received
    }
    subject._remove_properties_from_pending_updates({"1": True, "2": True, "3": False})
    assert subject._pending_updates == {
        "2": {"value": True, "updated_at": now, "sent": False},
        "3": {"value": True, "updated_at": now, "sent": True},
        "4": {"value": True, "updated_at": now, "sent": True},
    }


def test_actually_start(subject, mocker, patched_hass):
    # Set up the preconditions
    mocker.patch.object(subject, "receive_loop", return_value="LOOP")
    mocker.patch.object(subject, "_refresh_task", new=mocker.AsyncMock)
    subject._running = False
    mocker.patch.object(patched_hass, "async_create_task")
    # patched_hass.async_create_task = mocker.MagicMock()
    # patched_hass.bus.async_listen_once = mocker.AsyncMock()
    # patched_hass.bus.async_listen_once.return_value = "LISTENER"
    # run the function under test
    subject.actually_start()

    # did it register a listener for EVENT_HOMEASSISTANT_STOP?
    # patched_hass.bus.async_listen_once.assert_called_once_with(
    #     EVENT_HOMEASSISTANT_STOP, subject.async_stop
    # )
    # assert subject._shutdown_listener == "LISTENER"
    # did it set the running flag?
    assert subject._running
    # did it schedule the loop?
    # task.assert_called_once()


def test_start_starts_when_ha_running(subject, patched_hass, mocker):
    # Set up preconditions
    patched_hass.is_running = True
    listener = mocker.MagicMock()
    subject._startup_listener = listener
    subject.actually_start = mocker.MagicMock()

    # Call the function under test
    subject.start()

    # Did it actually start?
    subject.actually_start.assert_called_once()
    # Did it cancel the startup listener?
    assert subject._startup_listener is None
    listener.assert_called_once()


def test_start_schedules_for_later_when_ha_starting(subject, patched_hass, mocker):
    # Set up preconditions
    patched_hass.is_running = False
    subject.actually_start = mocker.MagicMock()

    # Call the function under test
    subject.start()

    # Did it avoid actually starting?
    subject.actually_start.assert_not_called()
    # Did it register a listener?
    # assert subject._startup_listener == "LISTENER"
    # patched_hass.bus.async_listen_once.assert_called_once_with(
    #     EVENT_HOMEASSISTANT_STARTED, subject.actually_start
    # )


def test_start_does_nothing_when_ha_stopping(subject, patched_hass, mocker):
    # Set up preconditions
    patched_hass.is_running = True
    patched_hass.is_stopping = True
    subject.actually_start = mocker.MagicMock()

    # Call the function under test
    subject.start()

    # Did it avoid actually starting?
    subject.actually_start.assert_not_called()
    # Did it avoid registering a listener?
    # patched_hass.bus.async_listen_once.assert_not_called()
    assert subject._startup_listener is None


@pytest.mark.asyncio
async def test_async_stop(subject, mocker):
    # Set up preconditions
    listener = mocker.MagicMock()
    subject._refresh_task = None
    subject._shutdown_listener = listener
    subject._children = [1, 2, 3]

    # Call the function under test
    await subject.async_stop()

    # Shutdown listener doesn't get cancelled as HA does that
    listener.assert_not_called()
    # Were the child entities cleared?
    assert subject._children == []
    # Did it wait for the refresh task to finish then clear it?
    # This doesn't work because AsyncMock only mocks awaitable method calls
    # but we want an awaitable object
    # refresh.assert_awaited_once()
    assert subject._refresh_task is None


@pytest.mark.asyncio
async def test_async_stop_when_not_running(subject):
    # Set up preconditions
    _refresh_task = None
    subject._shutdown_listener = None
    subject._children = []

    # Call the function under test
    await subject.async_stop()

    # Was the shutdown listener left empty?
    assert subject._shutdown_listener is None
    # Were the child entities cleared?
    assert subject._children == []
    # Was the refresh task left empty?
    assert subject._refresh_task is None


def test_register_first_entity_ha_running(subject, mocker):
    # Set up preconditions
    subject._children = []
    subject._running = False
    subject._startup_listener = None
    subject.start = mocker.MagicMock()
    entity = mocker.AsyncMock()
    entity._config = mocker.MagicMock()
    entity._config.dps.return_value = []
    # despite the name, the below HA function is not async and does not need to be awaited
    entity.async_schedule_update_ha_state = mocker.MagicMock()

    # Call the function under test
    subject.register_entity(entity)

    # Was the entity added to the list?
    assert subject._children == [entity]

    # Did we start the loop?
    subject.start.assert_called_once()


def test_register_subsequent_entity_ha_running(subject, mocker):
    # Set up preconditions
    first = mocker.AsyncMock()
    second = mocker.AsyncMock()
    second._config = mocker.MagicMock()
    second._config.dps.return_value = []
    subject._children = [first]
    subject._running = True

    subject._startup_listener = None
    subject.start = mocker.MagicMock()

    # Call the function under test
    subject.register_entity(second)

    # Was the entity added to the list?
    assert set(subject._children) == set([first, second])

    # Did we avoid restarting the loop?
    subject.start.assert_not_called()


def test_register_subsequent_entity_ha_starting(subject, mocker):
    # Set up preconditions
    first = mocker.AsyncMock()
    second = mocker.AsyncMock()
    second._config = mocker.MagicMock()
    second._config.dps.return_value = []
    subject._children = [first]
    subject._running = False
    subject._startup_listener = mocker.MagicMock()
    subject.start = mocker.MagicMock()

    # Call the function under test
    subject.register_entity(second)

    # Was the entity added to the list?
    assert set(subject._children) == set([first, second])
    # Did we avoid restarting the loop?
    subject.start.assert_not_called()


@pytest.mark.asyncio
async def test_unregister_one_of_many_entities(subject, mocker):
    # Set up preconditions
    subject._children = ["First", "Second"]
    subject.async_stop = mocker.AsyncMock()

    # Call the function under test
    await subject.async_unregister_entity("First")

    # Was the entity removed from the list?
    assert set(subject._children) == set(["Second"])
    # Is the loop still running?
    subject.async_stop.assert_not_called()


@pytest.mark.asyncio
async def test_unregister_last_entity(subject, mocker):
    # Set up preconditions
    subject._children = ["Last"]
    subject.async_stop = mocker.AsyncMock()

    # Call the function under test
    await subject.async_unregister_entity("Last")

    # Was the entity removed from the list?
    assert subject._children == []
    # Was the loop stopped?
    subject.async_stop.assert_called_once()


@pytest.mark.asyncio
async def test_async_receive(subject, mock_api, mocker):
    # Set up preconditions
    mock_api().status.return_value = {"dps": {"1": "INIT", "2": 2}}
    mock_api().receive.return_value = {"1": "UPDATED"}
    subject._running = True
    subject._cached_state = {"updated_at": 0}
    # Call the function under test
    print("starting test loop...")
    loop = subject.async_receive()
    print("getting first iteration...")
    result = await loop.__anext__()

    # Check that the loop was started, but without persistent connection
    # since there was no state returned yet and it might need to negotiate
    # version.
    mock_api().set_socketPersistent.assert_called_once_with(False)
    # Check that a full poll was done
    mock_api().status.assert_called_once()
    assert result == {"1": "INIT", "2": 2, "full_poll": mocker.ANY}
    # Prepare for next round
    subject._cached_state = subject._cached_state | result
    mock_api().set_socketPersistent.reset_mock()
    mock_api().status.reset_mock()
    subject._cached_state["updated_at"] = time()

    # Call the function under test
    print("getting second iteration...")
    result = await loop.__anext__()

    # Check that a heartbeat poll was done
    mock_api().status.assert_not_called()
    mock_api().heartbeat.assert_called_once()
    mock_api().receive.assert_called_once()
    assert result == {"1": "UPDATED", "full_poll": mocker.ANY}
    # Check that the connection was made persistent now that data has been
    # returned
    mock_api().set_socketPersistent.assert_called_once_with(True)
    # Prepare for next iteration
    subject._running = False
    mock_api().set_socketPersistent.reset_mock()

    # Call the function under test
    print("getting last iteration...")
    try:
        result = await loop.__anext__()
        pytest.fail("Should have raised an exception to quit the loop")
    # Check that the loop terminated
    except StopAsyncIteration:
        pass
    mock_api().set_socketPersistent.assert_called_once_with(False)


def test_should_poll(subject):
    subject._cached_state = {"1": "sample", "updated_at": time()}
    subject._poll_only = False
    subject._temporary_poll = False

    # Test temporary poll via pause/resume
    assert not subject.should_poll
    subject.pause()
    assert subject.should_poll
    subject.resume()
    assert not subject.should_poll

    # Test configured polling
    subject._poll_only = True
    assert subject.should_poll
    subject._poll_only = False

    # Test initial polling
    subject._cached_state = {}
    assert subject.should_poll
