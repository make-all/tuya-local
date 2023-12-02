from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from custom_components.tuya_local.device import TuyaLocalDevice


@asynccontextmanager
async def assert_device_properties_set(
    device: TuyaLocalDevice, properties: dict, msg=None
):
    results = []
    provided = {}

    def generate_result(*args):
        result = AsyncMock()
        results.append(result)
        provided[args[0]] = args[1]
        return result()

    def generate_results(*args):
        result = AsyncMock()
        results.append(result)
        provided.update(args[0])
        return result()

    device.async_set_property.side_effect = generate_result
    device.async_set_properties.side_effect = generate_results
    try:
        yield
    finally:
        if not msg:
            msg = f"Expected {properties}, got {provided}"
        assert len(provided) == len(properties.keys()), msg
        for p in properties:
            assert p in provided, msg
            assert properties[p] == provided[p], msg

        for result in results:
            result.assert_awaited()


@asynccontextmanager
async def assert_device_properties_set_optional(
    device: TuyaLocalDevice,
    properties: dict,
    optional_properties: dict,
):
    results = []
    provided = {}

    def generate_result(*args):
        result = AsyncMock()
        results.append(result)
        provided[args[0]] = args[1]
        return result()

    def generate_results(*args):
        result = AsyncMock()
        results.append(result)
        provided.update(args[0])
        return result()

    device.async_set_property.side_effect = generate_result
    device.async_set_properties.side_effect = generate_results
    try:
        yield
    finally:
        assert len(provided) >= len(properties.keys()) and (
            len(provided) <= len(properties.keys()) + len(optional_properties.keys())
        )
        for p in properties:
            assert p in provided
            assert properties[p] == provided[p]
        for p in optional_properties:
            if p in provided:
                assert optional_properties[p] == provided[p]

        for result in results:
            result.assert_awaited()
