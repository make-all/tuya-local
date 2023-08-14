"""
Setup for different kinds of Tuya button devices
"""
import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity

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
        "button",
        TuyaLocalButton,
    )


class TuyaLocalButton(TuyaLocalEntity, ButtonEntity):
    """Representation of a Tuya Button"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the button.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The config portion for this entity.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._button_dp = dps_map.pop("button")
        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class for this device"""
        dclass = self._config.device_class
        try:
            return ButtonDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(
                    "Unrecognized button device class of %s ignored",
                    dclass,
                )

    async def async_press(self):
        """Press the button"""
        await self._button_dp.async_set_value(self._device, True)
