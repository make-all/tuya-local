from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from custom_components.goldair_climate.device import GoldairTuyaDevice


@asynccontextmanager
async def assert_device_properties_set(device: GoldairTuyaDevice, properties: dict):
    result = AsyncMock()
    device.async_set_property.return_value = result()

    try:
        yield
    finally:
        for key in properties.keys():
            device.async_set_property.assert_called_once_with(key, properties[key])
        result.assert_awaited()
