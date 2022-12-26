"""
Platform to control Tuya buttons.
Buttons provide a way to send data to a Tuya dp which may not itself
be readable.  If the device does not return any state for the dp, then
it should be set as optional so it is not required to be present for detection.
"""
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity


class TuyaLocalButton(TuyaLocalEntity, ButtonEntity):
    """Representation of a Tuya Button"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the button.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The config portion for this entity.
        """
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
                _LOGGER.warning(f"Unrecognized button device class of {dclass} ignored")

    async def async_press(self):
        """Press the button"""
        await self._button_dp.async_set_value(self._device, True)
