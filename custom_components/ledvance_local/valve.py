"""
Support for Tuya valve devices
"""

import logging

from homeassistant.components.valve import (
    ValveDeviceClass,
    ValveEntity,
    ValveEntityFeature,
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
        "valve",
        TuyaLocalValve,
    )


class TuyaLocalValve(TuyaLocalEntity, ValveEntity):
    """Representation of a Tuya Valve"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the valve.
        Args:
            device (TuyaLocalDevice): The device API instance.
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._valve_dp = dps_map.pop("valve")
        self._switch_dp = dps_map.pop("switch", None)
        self._init_end(dps_map)

        if not self._valve_dp.readonly or self._switch_dp:
            self._attr_supported_features |= ValveEntityFeature.OPEN
            self._attr_supported_features |= ValveEntityFeature.CLOSE
            if self._valve_dp.type is int or (
                self._valve_dp.values(device)
                and self._valve_dp.values(device)[0] is int
            ):
                self._attr_supported_features |= ValveEntityFeature.SET_POSITION

    # HA defines translated names for valve classes, but does not use them
    def _default_to_device_class_name(self) -> bool:
        """Return True if an unnamed entity should be named by its device class.

        For valves we make this True if the entity has a device class.
        """
        return self.device_class is not None

    @property
    def device_class(self):
        """Return the class of this device"""
        dclass = self._config.device_class
        try:
            return ValveDeviceClass(dclass)
        except ValueError:
            if dclass:
                _LOGGER.warning(
                    "%s/%s: Unrecognised valve device class of %s ignored",
                    self._config._device.config,
                    self.name or "valve",
                    dclass,
                )

    @property
    def reports_position(self):
        """If the valve is an integer, it reports position."""
        return self._valve_dp.type is int or (
            self._valve_dp.values(self._device)
            and self._valve_dp.values(self._device)[0] is int
        )

    @property
    def current_position(self):
        """Report the position of the valve."""
        pos = self._valve_dp.get_value(self._device)
        if isinstance(pos, int):
            return pos

    @property
    def is_closed(self):
        """Report whether the valve is closed."""
        if self._switch_dp and self._switch_dp.get_value(self._device) is False:
            return True
        pos = self._valve_dp.get_value(self._device)
        return not pos

    async def async_open_valve(self):
        """Open the valve."""
        if self._switch_dp:
            _LOGGER.info("%s opening valve", self._config.config_id)
            await self._switch_dp.async_set_value(self._device, True)
            if self._valve_dp.get_value(self._device):
                return
        _LOGGER.info("%s fully opening valve", self._config.config_id)
        await self._valve_dp.async_set_value(
            self._device,
            100 if self.reports_position else True,
        )

    async def async_close_valve(self):
        """Close the valve"""
        if self._switch_dp:
            _LOGGER.info("%s closing valve", self._config.config_id)
            await self._switch_dp.async_set_value(self._device, False)
        else:
            _LOGGER.info("%s closing valve to 0%%", self._config.config_id)
            await self._valve_dp.async_set_value(
                self._device,
                0 if self.reports_position else False,
            )

    async def async_set_valve_position(self, position):
        """Set the position of the valve"""
        if not self.reports_position:
            raise NotImplementedError()
        _LOGGER.info(
            "%s setting valve position to %s%%", self._config.config_id, position
        )
        await self._valve_dp.async_set_value(self._device, position)
