from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass
from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    VacuumEntityFeature,
)
from homeassistant.const import AREA_SQUARE_METERS, PERCENTAGE, UnitOfTime

from ..const import LEFANT_M213_VACUUM_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
SWITCH_DPS = "2"
COMMAND_DPS = "3"
DIRECTION_DPS = "4"
STATUS_DPS = "5"
BATTERY_DPS = "6"
LOCATE_DPS = "13"
AREA_DPS = "16"
TIME_DPS = "17"
ERROR_DPS = "18"
FAN_DPS = "101"
UNKNOWN102_DPS = "102"
UNKNOWN103_DPS = "103"
UNKNOWN104_DPS = "104"
UNKNOWN106_DPS = "106"
UNKNOWN108_DPS = "108"


class TestLefantM213Vacuum(MultiSensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("lefant_m213_vacuum.yaml", LEFANT_M213_VACUUM_PAYLOAD)
        self.subject = self.entities.get("vacuum")
        self.setUpMultiSensors(
            [
                {
                    "dps": AREA_DPS,
                    "name": "sensor_clean_area",
                    "unit": AREA_SQUARE_METERS,
                },
                {
                    "dps": TIME_DPS,
                    "name": "sensor_clean_time",
                    "unit": UnitOfTime.MINUTES,
                    "device_class": SensorDeviceClass.DURATION,
                },
                {
                    "dps": BATTERY_DPS,
                    "name": "sensor_battery",
                    "unit": PERCENTAGE,
                    "device_class": SensorDeviceClass.BATTERY,
                    "state_class": STATE_CLASS_MEASUREMENT,
                },
            ],
        )
        self.mark_secondary(["sensor_clean_area", "sensor_clean_time"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                VacuumEntityFeature.STATE
                | VacuumEntityFeature.STATUS
                | VacuumEntityFeature.SEND_COMMAND
                | VacuumEntityFeature.TURN_ON
                | VacuumEntityFeature.TURN_OFF
                | VacuumEntityFeature.START
                | VacuumEntityFeature.PAUSE
                | VacuumEntityFeature.LOCATE
                | VacuumEntityFeature.RETURN_HOME
                | VacuumEntityFeature.CLEAN_SPOT
                | VacuumEntityFeature.FAN_SPEED
            ),
        )

    def test_fan_speed(self):
        self.dps[FAN_DPS] = "low"
        self.assertEqual(self.subject.fan_speed, "Low")
        self.dps[FAN_DPS] = "nar"
        self.assertEqual(self.subject.fan_speed, "Medium")
        self.dps[FAN_DPS] = "high"
        self.assertEqual(self.subject.fan_speed, "High")

    def test_status(self):
        self.dps[STATUS_DPS] = "0"
        self.assertEqual(self.subject.status, "paused")
        self.dps[STATUS_DPS] = "1"
        self.assertEqual(self.subject.status, "smart")
        self.dps[STATUS_DPS] = "2"
        self.assertEqual(self.subject.status, "wall follow")
        self.dps[STATUS_DPS] = "3"
        self.assertEqual(self.subject.status, "spiral")
        self.dps[STATUS_DPS] = "4"
        self.assertEqual(self.subject.status, "returning")
        self.dps[STATUS_DPS] = "5"
        self.assertEqual(self.subject.status, "charging")
        self.dps[STATUS_DPS] = "6"
        self.assertEqual(self.subject.status, "random")
        self.dps[STATUS_DPS] = "7"
        self.assertEqual(self.subject.status, "standby")

    def test_state(self):
        self.dps[POWER_DPS] = True
        self.dps[SWITCH_DPS] = True
        self.dps[ERROR_DPS] = 0
        self.dps[STATUS_DPS] = "4"
        self.assertEqual(self.subject.state, STATE_RETURNING)
        self.dps[STATUS_DPS] = "7"
        self.assertEqual(self.subject.state, STATE_IDLE)
        self.dps[STATUS_DPS] = "6"
        self.assertEqual(self.subject.state, STATE_CLEANING)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.state, STATE_IDLE)
        self.dps[POWER_DPS] = True
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.state, STATE_PAUSED)
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
