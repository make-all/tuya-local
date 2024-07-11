"""Tests for the ZX G30 Alarm Control Panel."""

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntityFeature as Feature,
)
from homeassistant.const import (
    STATE_ALARM_DISARMED,
)

from ..const import ZXG30_ALARM_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

ALARMSTATE_DP = "1"
EXITDELAY_DP = "2"
SIRENDURATION_DP = "3"
SIRENTONE_DP = "4"
TAMPER_DP = "9"
VOICE_DP = "10"
POWER_DP = "15"
BATTERY_DP = "16"
LOWBATT_DP = "17"
NOTIFY_DP = "27"
ENTRYDELAY_DP = "28"
TICKDOWN_DP = "29"


class TestZXG30Alarm(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("zx_g30_alarm.yaml", ZXG30_ALARM_PAYLOAD)
        self.subject = self.entities["alarm_control_panel"]
        self.mark_secondary(
            [
                "button_disarm",
                "button_away_arm",
                "button_home_arm",
                "number_exit_delay",
                "binary_sensor_tamper",
                "switch_voice_prompt",
                "binary_sensor_plug",
                "binary_sensor_battery",
                "switch_alarm_call",
                "switch_alarm_sms",
                "switch_alarm_notification",
                "number_entry_delay",
                "switch_tick_down",
                "button_factory_reset",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            Feature.ARM_AWAY | Feature.ARM_HOME,
        )

    def test_state(self):
        self.dps[ALARMSTATE_DP] = "disarmed"
        self.assertEqual(self.subject.state, STATE_ALARM_DISARMED)

    async def test_arm_home(self):
        async with assert_device_properties_set(
            self.subject._device,
            {ALARMSTATE_DP: "home"},
        ):
            await self.subject.async_alarm_arm_home()

    async def test_arm_away(self):
        async with assert_device_properties_set(
            self.subject._device,
            {ALARMSTATE_DP: "arm"},
        ):
            await self.subject.async_alarm_arm_away()

    async def test_disarm(self):
        async with assert_device_properties_set(
            self.subject._device,
            {ALARMSTATE_DP: "disarmed"},
        ):
            await self.subject.async_alarm_disarm()

    async def test_arm_vacation_fails_when_not_supported(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_alarm_arm_vacation()

    async def test_trigger_fails_when_not_supported(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_alarm_trigger()
