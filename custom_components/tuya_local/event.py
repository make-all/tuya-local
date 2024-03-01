"""
Implementation of Tuya events
"""

import logging

from homeassistant.components.event import EventDeviceClass, EventEntity

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "event",
        TuyaLocalEvent,
    )


class TuyaLocalEvent(TuyaLocalEntity, EventEntity):
    """Representation of a Tuya Event"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the event.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._event_dp = dps_map.pop("event")
        self._init_end(dps_map)

        # Set up device_class via parent class attribute
        try:
            self._attr_device_class = EventDeviceClass(self._config.device_class)
        except ValueError:
            if self._config.device_class:
                _LOGGER.warning(
                    "%s/%s: Unreecognised event device class of %s ignored",
                    self._config._device.config,
                    self.name or "event",
                    self._config.device_class,
                )
        # Set up event_types via parent class attribute
        self._attr_event_types = self._event_dp.values(device)

    def on_receive(self, dps):
        """Trigger the event when dp is received"""
        if self._event_dp.id in dps:
            value = self._event_dp.get_value(self._device)
            if value is not None:
                self._trigger_event(
                    value,
                    self.extra_state_attributes,
                )
