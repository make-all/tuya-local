"""
Setup for different kinds of Tuya text entities
"""

import logging

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.components.text.const import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_PATTERN,
)

from .device import TuyaLocalDevice
from .entity import TuyaLocalEntity
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "text",
        TuyaLocalText,
    )


class TuyaLocalText(TuyaLocalEntity, TextEntity):
    """Representation of a Tuya Text Entity"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the text entity.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._value_dp = dps_map.pop("value")
        if self._value_dp is None:
            raise AttributeError(f"{config.config_id} is missing value dp")

        self._attr_mode = TextMode.PASSWORD if self._value_dp.hidden else TextMode.TEXT
        self._extra_info = {ATTR_MODE: self._attr_mode}

        range = self._value_dp.range(device, False)
        if range:
            self._attr_native_min = range[0]
            self._attr_native_max = range[1]
            self._extra_info[ATTR_MIN] = self._attr_native_min
            self._extra_info[ATTR_MAX] = self._attr_native_max

        if self._value_dp.rawtype == "hex":
            self._attr_pattern = "[0-9a-fA-F]*"
        elif self._value_dp.rawtype == "base64":
            self._attr_pattern = "[-A-Za-z0-9+/]*={0,3}"
        # TODO: general pattern support

        if hasattr(self, "_attr_pattern"):
            self._extra_info[ATTR_PATTERN] = self._attr_pattern

    @property
    def native_value(self) -> str | None:
        """Return the current value"""
        return self._value_dp.get_value(self._device)

    async def async_set_value(self, value: str) -> None:
        """Set the value"""
        await self._value_dp.async_set_value(self._device, value)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """As well as extra attributes specified in the config, also return info about the text."""
        return TuyaLocalEntity.extra_state_attributes.fget(self) | self._extra_info
