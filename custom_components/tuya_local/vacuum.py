"""
Setup for different kinds of Tuya vacuum cleaners
"""

from homeassistant.components.vacuum import (
    SERVICE_CLEAN_SPOT,
    SERVICE_RETURN_TO_BASE,
    SERVICE_STOP,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)

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
        "vacuum",
        TuyaLocalVacuum,
    )


class TuyaLocalVacuum(TuyaLocalEntity, StateVacuumEntity):
    """Representation of a Tuya Vacuum Cleaner"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the sensor.
        Args:
            device (TuyaLocalDevice): the device API instance.
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._status_dps = dps_map.get("status")
        self._command_dps = dps_map.get("command")
        self._locate_dps = dps_map.get("locate")
        self._power_dps = dps_map.get("power")
        self._activate_dps = dps_map.get("activate")
        self._direction_dps = dps_map.get("direction_control")
        self._error_dps = dps_map.get("error")
        self._fan_dps = dps_map.pop("fan_speed", None)

        if self._status_dps is None:
            raise AttributeError(f"{config.config_id} is missing a status dps")
        self._init_end(dps_map)

    @property
    def supported_features(self):
        """Return the features supported by this vacuum cleaner."""
        support = (
            VacuumEntityFeature.STATE
            | VacuumEntityFeature.STATUS
            | VacuumEntityFeature.SEND_COMMAND
        )
        if self._fan_dps:
            support |= VacuumEntityFeature.FAN_SPEED
        if self._power_dps:
            support |= VacuumEntityFeature.TURN_ON | VacuumEntityFeature.TURN_OFF
        if self._locate_dps:
            support |= VacuumEntityFeature.LOCATE

        cmd_dps = self._command_dps or self._status_dps
        cmd_support = cmd_dps.values(self._device)
        if SERVICE_RETURN_TO_BASE in cmd_support:
            support |= VacuumEntityFeature.RETURN_HOME
        if SERVICE_CLEAN_SPOT in cmd_support:
            support |= VacuumEntityFeature.CLEAN_SPOT
        if SERVICE_STOP in cmd_support:
            support |= VacuumEntityFeature.STOP

        if self._activate_dps:
            support |= VacuumEntityFeature.START | VacuumEntityFeature.PAUSE
        else:
            if "start" in cmd_support:
                support |= VacuumEntityFeature.START
            if "pause" in cmd_support:
                support |= VacuumEntityFeature.PAUSE

        return support

    @property
    def status(self):
        """Return the status of the vacuum cleaner."""
        return self._status_dps.get_value(self._device)

    @property
    def state(self):
        """Return the state of the vacuum cleaner."""
        status = self.status
        if self._error_dps and self._error_dps.get_value(self._device):
            return STATE_ERROR
        elif status in [SERVICE_RETURN_TO_BASE, "returning"]:
            return STATE_RETURNING
        elif status in ["standby", "sleep"]:
            return STATE_IDLE
        elif status == "paused":
            return STATE_PAUSED
        elif status in ["charging", "charged"]:
            return STATE_DOCKED
        elif self._power_dps and self._power_dps.get_value(self._device) is False:
            return STATE_IDLE
        elif self._activate_dps and self._activate_dps.get_value(self._device) is False:
            return STATE_PAUSED
        else:
            return STATE_CLEANING

    async def async_turn_on(self, **kwargs):
        """Turn on the vacuum cleaner."""
        if self._power_dps:
            await self._power_dps.async_set_value(self._device, True)

    async def async_turn_off(self, **kwargs):
        """Turn off the vacuum cleaner."""
        if self._power_dps:
            await self._power_dps.async_set_value(self._device, False)

    async def async_toggle(self, **kwargs):
        """Toggle the vacuum cleaner."""
        dps = self._power_dps or self._activate_dps
        if dps:
            switch_to = not dps.get_value(self._device)
            await dps.async_set_value(self._device, switch_to)

    async def async_start(self):
        dps = self._command_dps or self._status_dps
        if dps and "start" in dps.values(self._device):
            await dps.async_set_value(self._device, "start")
        elif self._activate_dps:
            await self._activate_dps.async_set_value(self._device, True)

    async def async_pause(self):
        """Pause the vacuum cleaner."""
        dps = self._command_dps or self._status_dps
        if dps and "pause" in dps.values(self._device):
            await dps.async_set_value(self._device, "pause")
        elif self._activate_dps:
            await self._activate_dps.async_set_value(self._device, False)

    async def async_return_to_base(self, **kwargs):
        """Tell the vacuum cleaner to return to its base."""
        dps = self._command_dps or self._status_dps
        if dps and SERVICE_RETURN_TO_BASE in dps.values(self._device):
            await dps.async_set_value(self._device, SERVICE_RETURN_TO_BASE)

    async def async_clean_spot(self, **kwargs):
        """Tell the vacuum cleaner do a spot clean."""
        dps = self._command_dps or self._status_dps
        if dps and SERVICE_CLEAN_SPOT in dps.values(self._device):
            await dps.async_set_value(self._device, SERVICE_CLEAN_SPOT)

    async def async_stop(self, **kwargs):
        """Tell the vacuum cleaner to stop."""
        dps = self._command_dps or self._status_dps
        if dps and SERVICE_STOP in dps.values(self._device):
            await dps.async_set_value(self._device, SERVICE_STOP)

    async def async_locate(self, **kwargs):
        """Locate the vacuum cleaner."""
        if self._locate_dps:
            await self._locate_dps.async_set_value(self._device, True)

    async def async_send_command(self, command, params=None, **kwargs):
        """Send a command to the vacuum cleaner."""
        dps = self._command_dps or self._status_dps
        # stop command is often present in both command and direction dps
        # in that case, prefer the direction dp as async_stop will cover
        # the commad dp seperately.
        if (
            command == SERVICE_STOP
            and self._direction_dps
            and SERVICE_STOP in self._direction_dps.values(self._device)
        ):
            dps = self._direction_dps
        if command in dps.values(self._device):
            await dps.async_set_value(self._device, command)
        elif self._direction_dps and command in self._direction_dps.values(
            self._device
        ):
            await self._direction_dps.async_set_value(self._device, command)

    @property
    def fan_speed_list(self):
        """Return the list of fan speeds supported"""
        if self._fan_dps:
            return self._fan_dps.values(self._device)

    @property
    def fan_speed(self):
        """Return the current fan speed"""
        if self._fan_dps:
            return self._fan_dps.get_value(self._device)

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set the fan speed of the vacuum."""
        if self._fan_dps:
            await self._fan_dps.async_set_value(self._device, fan_speed)
