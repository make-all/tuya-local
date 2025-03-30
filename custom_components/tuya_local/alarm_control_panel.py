"""
Setup for different kinds of Tuya alarm control panels.
"""

import logging

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature as Feature,
)
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelState,
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
        "alarm_control_panel",
        TuyaLocalAlarmControlPanel,
    )


class TuyaLocalAlarmControlPanel(TuyaLocalEntity, AlarmControlPanelEntity):
    """Representation of a Tuya Alarm Control Panel"""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialise the alarm control panel.
        Args:
            device (TuyaLocalDevice): the device API instance
            config (TuyaEntityConfig): the configuration for this entity
        """
        super().__init__()
        dps_map = self._init_begin(device, config)
        self._alarm_state_dp = dps_map.get("alarm_state")
        self._trigger_dp = dps_map.get("trigger")

        self._init_end(dps_map)
        if not self._alarm_state_dp:
            raise AttributeError(f"{config.config_id} is missing an alarm_state dp")

        alarm_states = self._alarm_state_dp.values(device)
        if AlarmControlPanelState.ARMED_HOME in alarm_states:
            self._attr_supported_features |= Feature.ARM_HOME
        if AlarmControlPanelState.ARMED_AWAY in alarm_states:
            self._attr_supported_features |= Feature.ARM_AWAY
        if AlarmControlPanelState.ARMED_NIGHT in alarm_states:
            self._attr_supported_features |= Feature.ARM_NIGHT
        if AlarmControlPanelState.ARMED_VACATION in alarm_states:
            self._attr_supported_features |= Feature.ARM_VACATION
        if AlarmControlPanelState.ARMED_CUSTOM_BYPASS in alarm_states:
            self._attr_supported_features |= Feature.ARM_CUSTOM_BYPASS
        if self._trigger_dp:
            self._attr_supported_features |= Feature.TRIGGER
        # Code support not implemented
        self._attr_code_format = None
        self._attr_code_arm_required = False

    @property
    def alarm_state(self):
        """Return the current alarm state."""
        if self._trigger_dp and self._trigger_dp.get_value(self._device):
            return AlarmControlPanelState.TRIGGERED
        return AlarmControlPanelState(
            self._alarm_state_dp.get_value(self._device),
        )

    async def _alarm_send_command(self, cmd: str):
        if cmd in self._alarm_state_dp.values(self._device):
            await self._alarm_state_dp.async_set_value(self._device, cmd)
        else:
            raise NotImplementedError()

    async def async_alarm_disarm(self, code=None):
        """Send disarm command"""
        await self._alarm_send_command(AlarmControlPanelState.DISARMED)

    async def async_alarm_arm_home(self, code=None):
        await self._alarm_send_command(AlarmControlPanelState.ARMED_HOME)

    async def async_alarm_arm_away(self, code=None):
        """Send away command"""
        await self._alarm_send_command(AlarmControlPanelState.ARMED_AWAY)

    async def async_alarm_arm_night(self, code=None):
        """Send away command"""
        await self._alarm_send_command(AlarmControlPanelState.ARMED_NIGHT)

    async def async_alarm_arm_vacation(self, code=None):
        """Send away command"""
        await self._alarm_send_command(AlarmControlPanelState.ARMED_VACATION)

    async def async_alarm_arm_custom_bypass(self, code=None):
        await self._alarm_send_command(AlarmControlPanelState.ARMED_CUSTOM_BYPASS)

    async def async_alarm_trigger(self, code=None):
        if self._trigger_dp:
            await self._trigger_dp.async_set_value(self._device, True)
        else:
            await self._alarm_send_command(AlarmControlPanelState.TRIGGERED)
