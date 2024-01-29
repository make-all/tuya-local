from datetime import datetime
from time import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import ANY, AsyncMock, Mock, call, patch

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP

from custom_components.tuya_local.device import TuyaLocalDevice
from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig
from custom_components.tuya_local.switch import TuyaLocalSwitch

from .const import EUROM_600_HEATER_PAYLOAD


class TestDevice(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("tinytuya.Device")
        self.addCleanup(device_patcher.stop)
        self.mock_api = device_patcher.start()

        hass_patcher = patch("homeassistant.core.HomeAssistant")
        self.addCleanup(hass_patcher.stop)
        self.hass = hass_patcher.start()
        self.hass().is_running = True
        self.hass().is_stopping = False

        def job(func, *args):
            return func(*args)

        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.side_effect = job

        sleep_patcher = patch("asyncio.sleep")
        self.addCleanup(sleep_patcher.stop)
        self.mock_sleep = sleep_patcher.start()

        lock_patcher = patch("custom_components.tuya_local.device.Lock")
        self.addCleanup(lock_patcher.stop)
        self.mock_lock = lock_patcher.start()

        self.subject = TuyaLocalDevice(
            "Some name",
            "some_dev_id",
            "some.ip.address",
            "some_local_key",
            "auto",
            None,
            self.hass(),
        )
        # For most tests we want the protocol working
        self.subject._api_protocol_version_index = 0
        self.subject._api_protocol_working = True
        self.subject._protocol_configured = "auto"

    def test_configures_tinytuya_correctly(self):
        self.mock_api.assert_called_once_with(
            "some_dev_id", "some.ip.address", "some_local_key"
        )
        self.assertIs(self.subject._api, self.mock_api())

    def test_name(self):
        """Returns the name given at instantiation."""
        self.assertEqual(self.subject.name, "Some name")

    def test_unique_id(self):
        """Returns the unique ID presented by the API class."""
        self.assertIs(self.subject.unique_id, self.mock_api().id)

    def test_device_info(self):
        """Returns generic info plus the unique ID for categorisation."""
        self.assertEqual(
            self.subject.device_info,
            {
                "identifiers": {("tuya_local", self.mock_api().id)},
                "name": "Some name",
                "manufacturer": "Tuya",
            },
        )

    def test_has_returned_state(self):
        """Returns True if the device has returned its state."""
        self.subject._cached_state = EUROM_600_HEATER_PAYLOAD
        self.assertTrue(self.subject.has_returned_state)

        self.subject._cached_state = {"updated_at": 0}
        self.assertFalse(self.subject.has_returned_state)

    async def test_refreshes_state_if_no_cached_state_exists(self):
        self.subject._cached_state = {}
        self.subject.async_refresh = AsyncMock()

        await self.subject.async_inferred_type()

        self.subject.async_refresh.assert_awaited()

    async def test_detection_returns_none_when_device_type_not_detected(self):
        self.subject._cached_state = {"2": False, "updated_at": datetime.now()}
        self.assertEqual(await self.subject.async_inferred_type(), None)

    async def test_refreshes_when_there_is_no_pending_reset(self):
        self.subject._cached_state = {"updated_at": time() - 19}
        self.mock_api().status.return_value = {"dps": {"1": "called"}}

        await self.subject.async_refresh()

        self.mock_api().status.assert_called_once()
        self.assertEqual(self.subject._cached_state["1"], "called")

    async def test_refreshes_when_there_is_expired_pending_reset(self):
        self.subject._cached_state = {"updated_at": time() - 20}
        self.mock_api().status.return_value = {"dps": {"1": "called"}}

        await self.subject.async_refresh()

        self.mock_api().status.assert_called_once()
        self.assertEqual(self.subject._cached_state["1"], "called")

    async def test_refresh_retries_up_to_eleven_times(self):
        self.subject._api_protocol_working = False
        self.mock_api().status.side_effect = [
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

        await self.subject.async_refresh()

        self.assertEqual(self.mock_api().status.call_count, 11)
        self.assertEqual(self.subject._cached_state["1"], False)

    async def test_refresh_clears_cache_after_allowed_failures(self):
        self.subject._cached_state = {"1": True}
        self.subject._pending_updates = {
            "1": {"value": False, "updated_at": datetime.now(), "sent": True}
        }
        self.mock_api().status.side_effect = [
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
        ]

        await self.subject.async_refresh()

        self.assertEqual(self.mock_api().status.call_count, 3)
        self.assertEqual(self.subject._cached_state, {"updated_at": 0})
        self.assertEqual(self.subject._pending_updates, {})

    async def test_api_protocol_version_is_rotated_with_each_failure(self):
        self.subject._api_protocol_version_index = None
        self.subject._api_protocol_working = False
        self.mock_api().status.side_effect = [
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
        ]
        await self.subject.async_refresh()

        self.mock_api().set_version.assert_has_calls(
            [call(3.1), call(3.2), call(3.4), call(3.5), call(3.3), call(3.1)]
        )

    async def test_api_protocol_version_is_stable_once_successful(self):
        self.subject._api_protocol_version_index = None
        self.subject._api_protocol_working = False
        self.mock_api().status.side_effect = [
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            {"dps": {"1": False}},
            {"dps": {"1": False}},
            Exception("Error"),
            Exception("Error"),
            {"dps": {"1": False}},
        ]

        await self.subject.async_refresh()
        self.assertEqual(self.subject._api_protocol_version_index, 3)
        self.assertTrue(self.subject._api_protocol_working)
        await self.subject.async_refresh()
        self.assertEqual(self.subject._api_protocol_version_index, 3)
        await self.subject.async_refresh()
        self.assertEqual(self.subject._api_protocol_version_index, 3)

        self.mock_api().set_version.assert_has_calls(
            [
                call(3.1),
                call(3.2),
                call(3.4),
            ]
        )

    async def test_api_protocol_version_is_not_rotated_when_not_auto(self):
        # Set up preconditions for the test

        self.subject._protocol_configured = 3.4
        self.subject._api_protocol_version_index = None
        self.subject._api_protocol_working = False
        self.mock_api().status.side_effect = [
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
        await self.subject._rotate_api_protocol_version()
        self.mock_api().set_version.assert_called_once_with(3.4)
        self.mock_api().set_version.reset_mock()

        await self.subject.async_refresh()
        self.assertEqual(self.subject._api_protocol_version_index, 3)
        await self.subject.async_refresh()
        self.assertEqual(self.subject._api_protocol_version_index, 3)
        await self.subject.async_refresh()
        self.assertEqual(self.subject._api_protocol_version_index, 3)

    def test_reset_cached_state_clears_cached_state_and_pending_updates(self):
        self.subject._cached_state = {"1": True, "updated_at": time()}
        self.subject._pending_updates = {
            "1": {"value": False, "updated_at": datetime.now(), "sent": True}
        }

        self.subject._reset_cached_state()

        self.assertEqual(self.subject._cached_state, {"updated_at": 0})
        self.assertEqual(self.subject._pending_updates, {})

    def test_get_property_returns_value_from_cached_state(self):
        self.subject._cached_state = {"1": True}
        self.assertEqual(self.subject.get_property("1"), True)

    def test_get_property_returns_pending_update_value(self):
        self.subject._pending_updates = {
            "1": {"value": False, "updated_at": time() - 4, "sent": True}
        }
        self.assertEqual(self.subject.get_property("1"), False)

    def test_pending_update_value_overrides_cached_value(self):
        self.subject._cached_state = {"1": True}
        self.subject._pending_updates = {
            "1": {"value": False, "updated_at": time() - 4, "sent": True}
        }

        self.assertEqual(self.subject.get_property("1"), False)

    def test_expired_pending_update_value_does_not_override_cached_value(self):
        self.subject._cached_state = {"1": True}
        self.subject._pending_updates = {
            "1": {"value": False, "updated_at": time() - 5, "sent": True}
        }

        self.assertEqual(self.subject.get_property("1"), True)

    def test_get_property_returns_none_when_value_does_not_exist(self):
        self.subject._cached_state = {"1": True}
        self.assertIs(self.subject.get_property("2"), None)

    async def test_async_set_property_sends_to_api(self):
        await self.subject.async_set_property("1", False)

        self.mock_api().set_multiple_values.assert_called_once()

    async def test_set_property_immediately_stores_pending_updates(self):
        self.subject._cached_state = {"1": True}
        await self.subject.async_set_property("1", False)
        self.assertFalse(self.subject.get_property("1"))

    async def test_set_properties_takes_no_action_when_nothing_provided(self):
        with patch("asyncio.sleep") as mock:
            await self.subject.async_set_properties({})
            mock.assert_not_called()

    def test_anticipate_property_value_updates_cached_state(self):
        self.subject._cached_state = {"1": True}
        self.subject.anticipate_property_value("1", False)
        self.assertEqual(self.subject._cached_state["1"], False)

    def test_get_key_for_value_returns_key_from_object_matching_value(self):
        obj = {"key1": "value1", "key2": "value2"}

        self.assertEqual(
            TuyaLocalDevice.get_key_for_value(obj, "value1"),
            "key1",
        )
        self.assertEqual(
            TuyaLocalDevice.get_key_for_value(obj, "value2"),
            "key2",
        )

    def test_get_key_for_value_returns_fallback_when_value_not_found(self):
        obj = {"key1": "value1", "key2": "value2"}
        self.assertEqual(
            TuyaLocalDevice.get_key_for_value(obj, "value3", fallback="fb"),
            "fb",
        )

    def test_refresh_cached_state(self):
        # set up preconditions
        self.mock_api().status.return_value = {"dps": {"1": "CHANGED"}}
        self.subject._cached_state = {"1": "UNCHANGED", "updated_at": 123}

        # call the function under test
        self.subject._refresh_cached_state()

        # Did it call the API as expected?
        self.mock_api().status.assert_called_once()
        # Did it update the cached state?
        self.assertDictEqual(
            self.subject._cached_state,
            {"1": "CHANGED"} | self.subject._cached_state,
        )
        # Did it update the timestamp on the cached state?
        self.assertAlmostEqual(
            self.subject._cached_state["updated_at"],
            time(),
            delta=2,
        )

    def test_set_values(self):
        # set up preconditions
        self.subject._pending_updates = {
            "1": {"value": "sample", "updated_at": time() - 2, "sent": False},
        }

        # call the function under test
        self.subject._set_values({"1": "sample"})

        # did it send what it was asked?
        self.mock_api().set_multiple_values.assert_called_once_with(
            {"1": "sample"}, nowait=True
        )
        # did it mark the pending updates as sent?
        self.assertTrue(self.subject._pending_updates["1"]["sent"])
        # did it update the time on the pending updates?
        self.assertAlmostEqual(
            self.subject._pending_updates["1"]["updated_at"],
            time(),
            delta=2,
        )
        # did it lock and unlock when sending
        self.subject._lock.acquire.assert_called_once()
        self.subject._lock.release.assert_called_once()

    def test_pending_updates_cleared_on_receipt(self):
        # Set up the preconditions
        now = time()
        self.subject._pending_updates = {
            "1": {"value": True, "updated_at": now, "sent": True},
            "2": {"value": True, "updated_at": now, "sent": False},  # unsent
            "3": {"value": True, "updated_at": now, "sent": True},  # unmatched
            "4": {"value": True, "updated_at": now, "sent": True},  # not received
        }
        self.subject._remove_properties_from_pending_updates(
            {"1": True, "2": True, "3": False}
        )
        self.assertDictEqual(
            self.subject._pending_updates,
            {
                "2": {"value": True, "updated_at": now, "sent": False},
                "3": {"value": True, "updated_at": now, "sent": True},
                "4": {"value": True, "updated_at": now, "sent": True},
            },
        )

    def test_actually_start(self):
        # Set up the preconditions
        self.subject.receive_loop = Mock()
        self.subject.receive_loop.return_value = "LOOP"
        self.hass().bus.async_listen_once.return_value = "LISTENER"
        self.subject._running = False

        # run the function under test
        self.subject.actually_start()

        # did it register a listener for EVENT_HOMEASSISTANT_STOP?
        self.hass().bus.async_listen_once.assert_called_once_with(
            EVENT_HOMEASSISTANT_STOP, self.subject.async_stop
        )
        self.assertEqual(self.subject._shutdown_listener, "LISTENER")
        # did it set the running flag?
        self.assertTrue(self.subject._running)
        # did it schedule the loop?
        self.hass().async_create_task.assert_called_once_with("LOOP")

    def test_start_starts_when_ha_running(self):
        # Set up preconditions
        self.hass().is_running = True
        listener = Mock()
        self.subject._startup_listener = listener
        self.subject.actually_start = Mock()

        # Call the function under test
        self.subject.start()

        # Did it actually start?
        self.subject.actually_start.assert_called_once()
        # Did it cancel the startup listener?
        self.assertIsNone(self.subject._startup_listener)
        listener.assert_called_once()

    def test_start_schedules_for_later_when_ha_starting(self):
        # Set up preconditions
        self.hass().is_running = False
        self.hass().bus.async_listen_once.return_value = "LISTENER"
        self.subject.actually_start = Mock()

        # Call the function under test
        self.subject.start()

        # Did it avoid actually starting?
        self.subject.actually_start.assert_not_called()
        # Did it register a listener?
        self.assertEqual(self.subject._startup_listener, "LISTENER")
        self.hass().bus.async_listen_once.assert_called_once_with(
            EVENT_HOMEASSISTANT_STARTED, self.subject.actually_start
        )

    def test_start_does_nothing_when_ha_stopping(self):
        # Set up preconditions
        self.hass().is_running = True
        self.hass().is_stopping = True
        self.subject.actually_start = Mock()

        # Call the function under test
        self.subject.start()

        # Did it avoid actually starting?
        self.subject.actually_start.assert_not_called()
        # Did it avoid registering a listener?
        self.hass().bus.async_listen_once.assert_not_called()
        self.assertIsNone(self.subject._startup_listener)

    async def test_async_stop(self):
        # Set up preconditions
        listener = Mock()
        self.subject._refresh_task = None
        self.subject._shutdown_listener = listener
        self.subject._children = [1, 2, 3]

        # Call the function under test
        await self.subject.async_stop()

        # Shutdown listener doesn't get cancelled as HA does that
        listener.assert_not_called()
        # Were the child entities cleared?
        self.assertEqual(self.subject._children, [])
        # Did it wait for the refresh task to finish then clear it?
        # This doesn't work because AsyncMock only mocks awaitable method calls
        # but we want an awaitable object
        # refresh.assert_awaited_once()
        self.assertIsNone(self.subject._refresh_task)

    async def test_async_stop_when_not_running(self):
        # Set up preconditions
        self._refresh_task = None
        self.subject._shutdown_listener = None
        self.subject._children = []

        # Call the function under test
        await self.subject.async_stop()

        # Was the shutdown listener left empty?
        self.assertIsNone(self.subject._shutdown_listener)
        # Were the child entities cleared?
        self.assertEqual(self.subject._children, [])
        # Was the refresh task left empty?
        self.assertIsNone(self.subject._refresh_task)

    def test_register_first_entity_ha_running(self):
        # Set up preconditions
        self.subject._children = []
        self.subject._running = False
        self.subject._startup_listener = None
        self.subject.start = Mock()
        entity = AsyncMock()
        entity._config = Mock()
        entity._config.dps.return_value = []
        # despite the name, the below HA function is not async and does not need to be awaited
        entity.async_schedule_update_ha_state = Mock()

        # Call the function under test
        self.subject.register_entity(entity)

        # Was the entity added to the list?
        self.assertEqual(self.subject._children, [entity])

        # Did we start the loop?
        self.subject.start.assert_called_once()

    def test_register_subsequent_entity_ha_running(self):
        # Set up preconditions
        first = AsyncMock()
        second = AsyncMock()
        second._config = Mock()
        second._config.dps.return_value = []
        self.subject._children = [first]
        self.subject._running = True
        self.subject._startup_listener = None
        self.subject.start = Mock()

        # Call the function under test
        self.subject.register_entity(second)

        # Was the entity added to the list?
        self.assertCountEqual(self.subject._children, [first, second])

        # Did we avoid restarting the loop?
        self.subject.start.assert_not_called()

    def test_register_subsequent_entity_ha_starting(self):
        # Set up preconditions
        first = AsyncMock()
        second = AsyncMock()
        second._config = Mock()
        second._config.dps.return_value = []
        self.subject._children = [first]
        self.subject._running = False
        self.subject._startup_listener = Mock()
        self.subject.start = Mock()

        # Call the function under test
        self.subject.register_entity(second)

        # Was the entity added to the list?
        self.assertCountEqual(self.subject._children, [first, second])
        # Did we avoid restarting the loop?
        self.subject.start.assert_not_called()

    async def test_unregister_one_of_many_entities(self):
        # Set up preconditions
        self.subject._children = ["First", "Second"]
        self.subject.async_stop = AsyncMock()

        # Call the function under test
        await self.subject.async_unregister_entity("First")

        # Was the entity removed from the list?
        self.assertCountEqual(self.subject._children, ["Second"])
        # Is the loop still running?
        self.subject.async_stop.assert_not_called()

    async def test_unregister_last_entity(self):
        # Set up preconditions
        self.subject._children = ["Last"]
        self.subject.async_stop = AsyncMock()

        # Call the function under test
        await self.subject.async_unregister_entity("Last")

        # Was the entity removed from the list?
        self.assertEqual(self.subject._children, [])
        # Was the loop stopped?
        self.subject.async_stop.assert_called_once()

    async def test_async_receive(self):
        # Set up preconditions
        self.mock_api().status.return_value = {"dps": {"1": "INIT", "2": 2}}
        self.mock_api().receive.return_value = {"1": "UPDATED"}
        self.subject._running = True
        self.subject._cached_state = {"updated_at": 0}
        # Call the function under test
        print("starting test loop...")
        loop = self.subject.async_receive()
        print("getting first iteration...")
        result = await loop.__anext__()

        # Check that the loop was started, but without persistent connection
        # since there was no state returned yet and it might need to negotiate
        # version.
        self.mock_api().set_socketPersistent.assert_called_once_with(False)
        # Check that a full poll was done
        self.mock_api().status.assert_called_once()
        self.assertDictEqual(result, {"1": "INIT", "2": 2, "full_poll": ANY})
        # Prepare for next round
        self.subject._cached_state = self.subject._cached_state | result
        self.mock_api().set_socketPersistent.reset_mock()
        self.mock_api().status.reset_mock()
        self.subject._cached_state["updated_at"] = time()

        # Call the function under test
        print("getting second iteration...")
        result = await loop.__anext__()

        # Check that a heartbeat poll was done
        self.mock_api().status.assert_not_called()
        self.mock_api().heartbeat.assert_called_once()
        self.mock_api().receive.assert_called_once()
        self.assertDictEqual(result, {"1": "UPDATED", "full_poll": ANY})
        # Check that the connection was made persistent now that data has been
        # returned
        self.mock_api().set_socketPersistent.assert_called_once_with(True)
        # Prepare for next iteration
        self.subject._running = False
        self.mock_api().set_socketPersistent.reset_mock()

        # Call the function under test
        print("getting last iteration...")
        try:
            result = await loop.__anext__()
            self.fail("Should have raised an exception to quit the loop")
        # Check that the loop terminated
        except StopAsyncIteration:
            pass
        self.mock_api().set_socketPersistent.assert_called_once_with(False)

    def test_should_poll(self):
        self.subject._cached_state = {"1": "sample", "updated_at": time()}
        self.subject._poll_only = False
        self.subject._temporary_poll = False

        # Test temporary poll via pause/resume
        self.assertFalse(self.subject.should_poll)
        self.subject.pause()
        self.assertTrue(self.subject.should_poll)
        self.subject.resume()
        self.assertFalse(self.subject.should_poll)

        # Test configured polling
        self.subject._poll_only = True
        self.assertTrue(self.subject.should_poll)
        self.subject._poll_only = False

        # Test initial polling
        self.subject._cached_state = {}
        self.assertTrue(self.subject.should_poll)
