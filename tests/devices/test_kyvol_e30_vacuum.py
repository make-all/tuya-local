from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_CLEAN_SPOT,
    SUPPORT_FAN_SPEED,
    SUPPORT_LOCATE,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_SEND_COMMAND,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
)
from homeassistant.const import (
    TIME_MINUTES,
    PERCENTAGE,
)

from ..const import KYVOL_E30_VACUUM_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
SWITCH_DPS = "2"
COMMAND_DPS = "3"
DIRECTION_DPS = "4"
STATUS_DPS = "5"
BATTERY_DPS = "6"
EDGE_DPS = "7"
ROLL_DPS = "8"
FILTER_DPS = "9"
RSTEDGE_DPS = "10"
RSTROLL_DPS = "11"
RSTFILTER_DPS = "12"
LOCATE_DPS = "13"
FAN_DPS = "14"
TIME_DPS = "17"
ERROR_DPS = "18"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"
UNKNOWN104_DPS = "104"
UNKNOWN106_DPS = "107"


class TestKyvolE30Vacuum(MultiSensorTests, MultiSwitchTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("kyvol_e30_vacuum.yaml", KYVOL_E30_VACUUM_PAYLOAD)
        self.subject = self.entities.get("vacuum")
        self.setUpMultiSensors(
            [
                {
                    "dps": TIME_DPS,
                    "name": "sensor_clean_time",
                    "unit": TIME_MINUTES,
                },
                {
                    "dps": EDGE_DPS,
                    "name": "sensor_edge_brush",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": ROLL_DPS,
                    "name": "sensor_roll_brush",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": FILTER_DPS,
                    "name": "sensor_filter",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": STATUS_DPS,
                    "name": "sensor_status",
                },
            ],
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": RSTEDGE_DPS,
                    "name": "switch_edge_brush_reset",
                },
                {
                    "dps": RSTROLL_DPS,
                    "name": "switch_roll_brush_reset",
                },
                {
                    "dps": RSTFILTER_DPS,
                    "name": "switch_filter_reset",
                },
            ],
        )
        self.mark_secondary(
            [
                "sensor_clean_time",
                "sensor_edge_brush",
                "sensor_roll_brush",
                "sensor_filter",
                "sensor_status",
                "switch_edge_brush_reset",
                "switch_roll_brush_reset",
                "switch_filter_reset",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_STATE
            | SUPPORT_STATUS
            | SUPPORT_SEND_COMMAND
            | SUPPORT_BATTERY
            | SUPPORT_FAN_SPEED
            | SUPPORT_TURN_ON
            | SUPPORT_TURN_OFF
            | SUPPORT_START
            | SUPPORT_PAUSE
            | SUPPORT_LOCATE
            | SUPPORT_RETURN_HOME
            | SUPPORT_CLEAN_SPOT,
        )

    def test_battery_level(self):
        self.dps[BATTERY_DPS] = 50
        self.assertEqual(self.subject.battery_level, 50)

    def test_status(self):
        self.dps[COMMAND_DPS] = "standby"
        self.assertEqual(self.subject.status, "standby")
        self.dps[COMMAND_DPS] = "smart"
        self.assertEqual(self.subject.status, "smart")
        self.dps[COMMAND_DPS] = "chargego"
        self.assertEqual(self.subject.status, "return_to_base")
        self.dps[COMMAND_DPS] = "random"
        self.assertEqual(self.subject.status, "random")
        self.dps[COMMAND_DPS] = "wall_follow"
        self.assertEqual(self.subject.status, "wall_follow")
        self.dps[COMMAND_DPS] = "spiral"
        self.assertEqual(self.subject.status, "clean_spot")

    def test_state(self):
        self.dps[POWER_DPS] = True
        self.dps[SWITCH_DPS] = True
        self.dps[ERROR_DPS] = 0
        self.dps[COMMAND_DPS] = "return_to_base"
        self.assertEqual(self.subject.state, STATE_RETURNING)
        self.dps[COMMAND_DPS] = "standby"
        self.assertEqual(self.subject.state, STATE_DOCKED)
        self.dps[COMMAND_DPS] = "random"
        self.assertEqual(self.subject.state, STATE_CLEANING)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.state, STATE_DOCKED)
        self.dps[POWER_DPS] = True
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.state, STATE_DOCKED)
        self.dps[ERROR_DPS] = 1
        self.assertEqual(self.subject.state, STATE_ERROR)

    async def test_async_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True},
        ):
            await self.subject.async_turn_on()

    async def test_async_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_turn_off()

    async def test_async_toggle(self):
        self.dps[POWER_DPS] = False
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True},
        ):
            await self.subject.async_toggle()

    async def test_async_start(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True},
        ):
            await self.subject.async_start()

    async def test_async_pause(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: False},
        ):
            await self.subject.async_pause()

    async def test_async_return_to_base(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "chargego"},
        ):
            await self.subject.async_return_to_base()

    async def test_async_clean_spot(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "spiral"},
        ):
            await self.subject.async_clean_spot()

    async def test_async_locate(self):
        async with assert_device_properties_set(
            self.subject._device,
            {LOCATE_DPS: True},
        ):
            await self.subject.async_locate()

    async def test_async_send_standby_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "standby"},
        ):
            await self.subject.async_send_command("standby")

    async def test_async_send_smart_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "smart"},
        ):
            await self.subject.async_send_command("smart")

    async def test_async_send_random_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "random"},
        ):
            await self.subject.async_send_command("random")

    async def test_async_send_wall_follow_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DPS: "wall_follow"},
        ):
            await self.subject.async_send_command("wall_follow")

    async def test_async_send_reverse_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "backward"},
        ):
            await self.subject.async_send_command("reverse")

    async def test_async_send_left_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "turn_left"},
        ):
            await self.subject.async_send_command("left")

    async def test_async_send_right_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "turn_right"},
        ):
            await self.subject.async_send_command("right")

    async def test_async_send_stop_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "stop"},
        ):
            await self.subject.async_send_command("stop")

    def test_fan_speed(self):
        self.dps[FAN_DPS] = "2"
        self.assertEqual(self.subject.fan_speed, "quiet")

    def test_fan_speed_list(self):
        self.assertCountEqual(
            self.subject.fan_speed_list,
            [
                "strong",
                "normal",
                "quiet",
                "gentle",
                "closed",
            ],
        )

    async def test_async_set_fan_speed(self):
        async with assert_device_properties_set(self.subject._device, {FAN_DPS: "3"}):
            await self.subject.async_set_fan_speed(fan_speed="gentle")
