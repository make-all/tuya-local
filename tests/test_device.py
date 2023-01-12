from datetime import datetime
from time import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, call, patch

from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
)

from custom_components.tuya_local.device import TuyaLocalDevice

from .const import (
    EUROM_600_HEATER_PAYLOAD,
)


class TestDevice(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("tinytuya.Device")
        self.addCleanup(device_patcher.stop)
        self.mock_api = device_patcher.start()

        hass_patcher = patch("homeassistant.core.HomeAssistant")
        self.addCleanup(hass_patcher.stop)
        self.hass = hass_patcher.start()

        lock_patcher = patch("custom_components.tuya_local.device.Lock")
        self.addCleanup(lock_patcher.stop)
        self.mock_lock = lock_patcher.start()

        self.subject = TuyaLocalDevice(
            "Some name",
            "some_dev_id",
            "some.ip.address",
            "some_local_key",
            "auto",
            self.hass(),
        )

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
        async_job = AsyncMock()
        self.subject._cached_state = {"updated_at": time() - 19}
        self.hass().async_add_executor_job.return_value = async_job()
        await self.subject.async_refresh()

        async_job.assert_awaited()

    async def test_refreshes_when_there_is_expired_pending_reset(self):
        async_job = AsyncMock()
        self.subject._cached_state = {"updated_at": time() - 20}
        self.hass().async_add_executor_job.return_value = async_job()
        await self.subject.async_refresh()

        async_job.assert_awaited()

    async def test_refresh_reloads_status_from_device(self):
        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.return_value = {"dps": {"1": False}}

        await self.subject.async_refresh()

        self.hass().async_add_executor_job.assert_called_once()

    async def test_refresh_retries_up_to_nine_times(self):
        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.side_effect = [
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

        self.assertEqual(self.hass().async_add_executor_job.call_count, 9)
        # self.assertEqual(self.subject._cached_state["1"], False)

    async def test_refresh_clears_cached_and_pending_after_nine_fails(
        self,
    ):
        self.subject._cached_state = {"1": True}
        self.subject._pending_updates = {
            "1": {"value": False, "updated_at": datetime.now(), "sent": True}
        }
        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.side_effect = [
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
        ]

        await self.subject.async_refresh()

        self.assertEqual(self.hass().async_add_executor_job.call_count, 9)
        self.assertEqual(self.subject._cached_state, {"updated_at": 0})
        self.assertEqual(self.subject._pending_updates, {})

    async def test_api_protocol_version_is_rotated_with_each_failure(self):
        self.mock_api().set_version.reset_mock()
        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.side_effect = [
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
            Exception("Error"),
        ]
        await self.subject.async_refresh()

        self.mock_api().set_version.assert_has_calls(
            [call(3.1), call(3.2), call(3.4), call(3.3), call(3.1)]
        )

    async def test_api_protocol_version_is_stable_once_successful(self):
        self.mock_api().set_version.reset_mock()
        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.side_effect = [
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
        self.subject._protocol_configured = 3.4
        self.subject._api_protocol_version_index = None
        self.mock_api().set_version.reset_mock()
        self.subject._rotate_api_protocol_version()
        self.mock_api().set_version.assert_called_once_with(3.4)
        self.mock_api().set_version.reset_mock()

        self.hass().async_add_executor_job = AsyncMock()
        self.hass().async_add_executor_job.side_effect = [
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

    async def test_async_set_property_schedules_job(self):
        async_job = AsyncMock()
        self.hass().async_add_executor_job.return_value = async_job()

        await self.subject.async_set_property("1", False)

        self.hass().async_add_executor_job.assert_called_once()
        async_job.assert_awaited()

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

    def test_send_payload(self):
        # set up preconditions
        self.subject._pending_updates = {
            "1": {"value": "sample", "updated_at": time() - 2, "sent": False},
        }

        # call the function under test
        self.subject._send_payload("PAYLOAD")

        # did it send what it was asked?
        self.mock_api().send.assert_called_once_with("PAYLOAD")
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
        self.hass().is_stopping = False
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
        self.hass().is_stopping = False
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

        # Was the shutdown listener cancelled?
        listener.assert_called_once()
        self.assertIsNone(self.subject._shutdown_listener)
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

        # Call the function under test
        self.subject.register_entity("Entity")

        # Was the entity added to the list?
        self.assertEqual(self.subject._children, ["Entity"])

        # Did we start the loop?
        self.subject.start.assert_called_once()

    def test_register_subsequent_entity_ha_running(self):
        # Set up preconditions
        self.subject._children = ["First"]
        self.subject._running = True
        self.subject._startup_listener = None
        self.subject.start = Mock()

        # Call the function under test
        self.subject.register_entity("Entity")

        # Was the entity added to the list?
        self.assertCountEqual(self.subject._children, ["First", "Entity"])

        # Did we avoid restarting the loop?
        self.subject.start.assert_not_called()

    def test_register_subsequent_entity_ha_starting(self):
        # Set up preconditions
        self.subject._children = ["First"]
        self.subject._running = False
        self.subject._startup_listener = Mock()
        self.subject.start = Mock()

        # Call the function under test
        self.subject.register_entity("Entity")

        # Was the entity added to the list?
        self.assertCountEqual(self.subject._children, ["First", "Entity"])
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
