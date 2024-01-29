"""
Setup for different kinds of Tuya selects
"""
from homeassistant.components.select import SelectEntity

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
        "select",
        TuyaLocalSelect,
    )


class TuyaLocalSelect(TuyaLocalEntity, SelectEntity):
    """Representation of a Tuya Select"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the select.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._option_dps = dps_map.pop("option")
        if self._option_dps is None:
            raise AttributeError(f"{config.config_id} is missing an option dps")
        if not self._option_dps.values(device):
            raise AttributeError(
                f"{config.config_id} does not have a mapping to a list of options"
            )
        self._init_end(dps_map)

    @property
    def options(self):
        "Return the list of possible options."
        return self._option_dps.values(self._device)

    @property
    def current_option(self):
        "Return the currently selected option"
        return self._option_dps.get_value(self._device)

    async def async_select_option(self, option):
        "Set the option"
        await self._option_dps.async_set_value(self._device, option)
