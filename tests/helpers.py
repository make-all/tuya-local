from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from custom_components.goldair_climate.device import GoldairTuyaDevice


@asynccontextmanager
async def assert_device_properties_set(device: GoldairTuyaDevice, properties: dict):
    results = []

    def generate_result(*args):
        result = AsyncMock()
        results.append(result)
        return result()

    device.async_set_property.side_effect = generate_result

    try:
        yield
    finally:
        assert device.async_set_property.call_count == len(properties.keys())
        for key in properties.keys():
            device.async_set_property.assert_any_call(key, properties[key])
        for result in results:
            result.assert_awaited()
