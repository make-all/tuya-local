"""
Platform to control Tuya switches.
Initially based on the Kogan Switch and secondary switch for Purline M100
heater open window detector toggle.
"""
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity


class TuyaLocalSwitch(TuyaLocalEntity, SwitchEntity):
    """Representation of a Tuya Switch"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the switch.
        Args:
            device (TuyaLocalDevice): The device API instance.
        """
        dps_map = self._init_begin(device, config)
        self._switch_dps = dps_map.pop("switch")
        self._power_dps = dps_map.get("current_power_w", None)
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

    @property
    def current_power_w(self):
        """Return the current power consumption in Watts."""
        if self._power_dps is None:
            return None

        pwr = self._power_dps.get_value(self._device)
        return pwr

    async def async_turn_on(self, **kwargs):
        """Turn the switch on"""
        await self._switch_dps.async_set_value(self._device, True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off"""
        await self._switch_dps.async_set_value(self._device, False)
