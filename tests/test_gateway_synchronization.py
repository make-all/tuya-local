"""Exercise real gateway call paths and executor threads with explicit barriers."""

import asyncio
import threading
from time import time
from unittest.mock import MagicMock

import pytest

from custom_components.tuya_local import cleanup_failed_device
from custom_components.tuya_local.const import DOMAIN
from custom_components.tuya_local.device import TuyaLocalDevice


class ObservedLock:
    """Delegate to the actual shared asyncio lock; observe attempts and ownership."""

    def __init__(self, lock):
        self.lock = lock
        self.owner = None
        self.attempts = {}

    def attempted(self, task):
        return self.attempts.setdefault(task, asyncio.Event())

    async def __aenter__(self):
        task = asyncio.current_task()
        self.attempted(task).set()
        await self.lock.acquire()
        self.owner = task
        return self

    async def __aexit__(self, *args):
        assert self.owner is asyncio.current_task()
        self.owner = None
        self.lock.release()

    def locked(self):
        return self.lock.locked()


class BlockingOperation:
    """Hold a real executor thread inside the first gateway operation."""

    def __init__(self, lock):
        self.loop = asyncio.get_running_loop()
        self.lock = lock
        self.owner = None
        self.entered = asyncio.Event()
        self.release = threading.Event()
        self.finished = threading.Event()
        self.thread_id = None

    def __call__(self, *args, **kwargs):
        assert self.lock.locked()
        assert self.lock.owner is self.owner
        self.thread_id = threading.get_ident()
        self.loop.call_soon_threadsafe(self.entered.set)
        try:
            assert self.release.wait(10), "Test did not release the gateway operation"
            return {"dps": {"47": True}}
        finally:
            self.finished.set()


async def wait(event):
    """Fail promptly if production code never reaches the expected barrier."""
    await asyncio.wait_for(event.wait(), 3)


@pytest.fixture
async def siblings(hass, mocker):
    # HA's test fixture executes MagicMock targets inline. Force every target
    # through a real executor, including mocked heartbeat/receive methods.
    loop = asyncio.get_running_loop()
    mocker.patch.object(
        hass,
        "async_add_executor_job",
        side_effect=lambda func, *args: loop.run_in_executor(None, func, *args),
    )
    hass.data[DOMAIN] = {}
    parent = MagicMock(name="gateway")
    parent.parent = None
    children = [MagicMock(name=f"child{i}", socket=None) for i in range(2)]
    for child in children:
        child.parent = parent
    factory = mocker.patch("tinytuya.Device", side_effect=[parent, *children])
    devices = [
        TuyaLocalDevice(name, "gateway", "host", "key", 3.5, cid, hass)
        for name, cid in (("YR05", "cid05"), ("YR02", "cid02"))
    ]
    assert factory.call_count == 3
    assert devices[0]._api.parent is devices[1]._api.parent is parent
    assert devices[0]._api_lock is devices[1]._api_lock
    assert factory.call_args_list[1].kwargs["cid"] == "cid05"
    assert factory.call_args_list[2].kwargs["cid"] == "cid02"
    # Observe the existing real shared lock, rather than simulating locking.
    lock = ObservedLock(devices[0]._api_lock)
    for device in devices:
        device._api_lock = lock
        device._api.status.return_value = {"dps": {"47": True}}
    return devices


@pytest.mark.parametrize("operation", ["refresh", "command", "cleanup", "pause"])
async def test_sibling_transaction_waits(hass, siblings, operation):
    first, second = siblings
    lock = first._api_lock
    blocked = BlockingOperation(lock)
    first._api.status.side_effect = blocked
    first_task = asyncio.create_task(first.async_refresh())
    blocked.owner = first_task
    other = None
    entered_second = threading.Event()

    def second_call(*args, **kwargs):
        assert blocked.finished.is_set()
        assert lock.owner is other
        assert lock.locked()
        entered_second.set()
        return {"dps": {"47": False}}

    try:
        await wait(blocked.entered)
        assert blocked.thread_id != threading.get_ident()
        if operation == "refresh":
            second._api.status.side_effect = second_call
            pending = second.async_refresh()
        elif operation == "command":
            second._api.set_multiple_values.side_effect = second_call
            second._add_properties_to_pending_updates({"71": "payload"})
            pending = second._send_pending_updates()
        elif operation == "cleanup":
            first._api.parent.set_socketPersistent.side_effect = second_call
            hass.data[DOMAIN]["gateway/cid02"] = {
                "tuyadevice": second._api,
                "tuyadevicelock": lock,
            }
            pending = cleanup_failed_device(hass, "gateway/cid02")
        else:
            first._api.parent.set_socketPersistent.side_effect = second_call
            pending = second.pause()
        other = asyncio.create_task(pending)
        # This barrier fires inside acquisition, immediately before the real
        # lock blocks. Removing the production acquisition fails this wait.
        await wait(lock.attempted(other))
        assert lock.owner is first_task
        assert not blocked.finished.is_set()
        assert not entered_second.is_set()
        assert not other.done()
        second._api.status.assert_not_called()
        second._api.set_multiple_values.assert_not_called()
        first._api.parent.set_socketPersistent.assert_not_called()
        if operation == "pause":
            assert second._temporary_poll
        blocked.release.set()
        await asyncio.wait_for(asyncio.gather(first_task, other), 3)
        assert entered_second.is_set()
        if operation == "command":
            second._api.set_multiple_values.assert_called_once_with(
                {"71": "payload"}, nowait=True
            )
        elif operation in ("cleanup", "pause"):
            first._api.parent.set_socketPersistent.assert_called_once_with(False)
        if operation == "pause":
            second.resume()
            assert not second._temporary_poll
        first._api.parent.set_version.assert_called_with(3.5)
    finally:
        blocked.release.set()
        await asyncio.gather(
            first_task, *([other] if other else []), return_exceptions=True
        )


async def test_retry_cleanup_keeps_transaction_ownership(siblings):
    first, second = siblings
    lock = first._api_lock
    blocked = BlockingOperation(lock)
    calls = 0

    def status():
        nonlocal calls
        calls += 1
        assert lock.owner is first_task
        if calls == 1:
            blocked()
            return {"Err": "902", "Error": "timeout"}
        return {"dps": {"47": True}}

    closed = []

    def close(persist):
        assert persist is False
        assert lock.owner is first_task
        assert asyncio.current_task() is first_task
        assert lock.locked()
        second._api.status.assert_not_called()
        closed.append(persist)

    first._api.status.side_effect = status
    first._api.parent.set_socketPersistent.side_effect = close
    first_task = asyncio.create_task(first.async_refresh())
    blocked.owner = first_task
    other = None
    try:
        await wait(blocked.entered)
        other = asyncio.create_task(second.async_refresh())
        await wait(lock.attempted(other))
        blocked.release.set()
        await asyncio.wait_for(asyncio.gather(first_task, other), 3)
        assert closed == [False]
        first._api.parent.set_socketPersistent.assert_called_once_with(False)
        assert first._api.status.call_count == 2
        second._api.status.assert_called_once()
    finally:
        blocked.release.set()
        await asyncio.gather(
            first_task, *([other] if other else []), return_exceptions=True
        )


@pytest.mark.parametrize("phase", ["heartbeat", "receive", "reconnect"])
async def test_receive_parent_socket_and_serialization(siblings, phase):
    first, second = siblings
    lock = first._api_lock
    first._cached_state = {"47": True, "updated_at": time() - 6}
    first._last_full_poll = time()
    first._running = True
    first._api.parent.socket = None if phase == "reconnect" else object()
    blocked = BlockingOperation(lock)
    stream = first.async_receive()
    first_task = None
    other = None
    calls = []

    def operation(name):
        def call(*args):
            assert lock.locked()
            assert lock.owner is first_task
            calls.append(name)
            if name == phase or (name == "status" and phase == "reconnect"):
                return blocked()
            return {"dps": {"47": False}}

        return call

    first._api.heartbeat.side_effect = operation("heartbeat")
    first._api.receive.side_effect = operation("receive")
    first._api.status.side_effect = operation("status")

    def sibling_status():
        assert blocked.finished.is_set()
        assert lock.owner is other
        return {"dps": {"47": True}}

    second._api.status.side_effect = sibling_status
    try:
        first_task = asyncio.create_task(anext(stream))
        blocked.owner = first_task
        await wait(blocked.entered)
        other = asyncio.create_task(second.async_refresh())
        await wait(lock.attempted(other))
        assert lock.owner is first_task
        second._api.status.assert_not_called()
        blocked.release.set()
        await asyncio.wait_for(asyncio.gather(first_task, other), 3)
        assert calls == (
            ["status"] if phase == "reconnect" else ["heartbeat", "receive"]
        )
        if phase != "reconnect":
            first._api.heartbeat.assert_called_once_with(True)
        # The generator is suspended at yield, yet the sibling has completed.
        assert not lock.locked()
    finally:
        blocked.release.set()
        await asyncio.gather(
            *([first_task] if first_task else []),
            *([other] if other else []),
            return_exceptions=True,
        )
        first._running = False
        await stream.aclose()


async def test_cancelled_refresh_retains_lock_until_thread_finishes(siblings, mocker):
    first, second = siblings
    lock = first._api_lock
    blocked = BlockingOperation(lock)
    first._api.status.side_effect = blocked
    draining = asyncio.Event()
    real_shield = asyncio.shield
    first_task = None
    other = None

    def shield(job):
        result = real_shield(job)
        if asyncio.current_task() is first_task and first_task.cancelling():
            # Observe the real cancellation handler re-awaiting its live job.
            draining.set()
        return result

    mocker.patch(
        "custom_components.tuya_local.device.asyncio.shield", side_effect=shield
    )

    def sibling_status():
        assert blocked.finished.is_set()
        assert first_task.cancelled()
        assert lock.owner is other
        return {"dps": {"47": True}}

    second._api.status.side_effect = sibling_status
    first_task = asyncio.create_task(first.async_refresh())
    blocked.owner = first_task
    try:
        await wait(blocked.entered)
        assert blocked.thread_id != threading.get_ident()
        first_task.cancel()
        await wait(draining)
        other = asyncio.create_task(second.async_refresh())
        await wait(lock.attempted(other))
        assert not blocked.finished.is_set()
        assert not first_task.done()
        assert lock.owner is first_task
        second._api.status.assert_not_called()
        blocked.release.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(first_task, 3)
        await asyncio.wait_for(other, 3)
        assert blocked.finished.is_set()
        assert not lock.locked()
        second._api.status.assert_called_once()
    finally:
        blocked.release.set()
        await asyncio.gather(
            first_task, *([other] if other else []), return_exceptions=True
        )
