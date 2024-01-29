"""
Setup for different kinds of Tuya switch devices
"""
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity

from .device import TuyaLocalDevice
from .helpers.config import async_tuya_setup_platform
from .helpers.device_config import TuyaEntityConfig
from .helpers.mixin import TuyaLocalEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    await async_tuya_setup_platform(
        hass,
        async_add_entities,
        config,
        "switch",
        TuyaLocalSwitch,
    )


class TuyaLocalSwitch(TuyaLocalEntity, SwitchEntity):
    """Representation of a Tuya Switch"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the switch.
        Args:
            device (TuyaLocalDevice): The device API instance.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._switch_dps = dps_map.pop("switch")
        self._init_end(dps_map)

    @property
    def device_class(self):
        """Return the class of this device"""
        return (
            SwitchDeviceClass.OUTLET
            if self._config.device_class == "outlet"
            else SwitchDeviceClass.SWITCH
        )

    @property
    def is_on(self):
        """Return whether the switch is on or not."""
        # if there is no switch, it is always on if available.
        if self._switch_dps is None:
            return self.available
        return self._switch_dps.get_value(self._device)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._switch_dps.async_set_value(self._device, True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._switch_dps.async_set_value(self._device, False)
