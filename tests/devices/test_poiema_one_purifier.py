from homeassistant.components.fan import SUPPORT_PRESET_MODE, SUPPORT_SET_SPEED
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    TIME_MINUTES,
)

from ..const import POIEMA_ONE_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.lock import BasicLockTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
PM25_DPS = "2"
MODE_DPS = "3"
SPEED_DPS = "4"
LOCK_DPS = "7"
RESET_DPS = "11"
TIMER_DPS = "18"
COUNTDOWN_DPS = "19"


class TestPoeimaOnePurifier(
    BasicLockTests,
    BasicSelectTests,
    BasicSwitchTests,
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("poiema_one_purifier.yaml", POIEMA_ONE_PURIFIER_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities.get("select_timer"),
            {
                "cancel": "off",
                "1h": "1 hour",
                "2h": "2 hours",
                "3h": "3 hours",
                "4h": "4 hours",
                "5h": "5 hours",
            },
        )
        self.setUpBasicSwitch(RESET_DPS, self.entities.get("switch_filter_reset"))
        self.setUpMultiSensors(
            [
                {
                    "dps": PM25_DPS,
                    "name": "sensor_pm2_5",
                    "device_class": SensorDeviceClass.PM25,
                    "state_class": "measurement",
                    "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                },
                {
                    "dps": COUNTDOWN_DPS,
                    "name": "sensor_timer",
                    "unit": TIME_MINUTES,
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "switch_filter_reset",
                "select_timer",
                "sensor_timer",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED,
        )

    def test_speed(self):
        self.dps[SPEED_DPS] = "low"
        self.assertEqual(self.subject.percentage, 25)

    def test_speed_step(self):
        self.assertEqual(self.subject.percentage_step, 25)

    async def test_set_speed(self):
        async with assert_device_properties_set(
            self.subject._device, {SPEED_DPS: "mid"}
        ):
            await self.subject.async_set_percentage(50)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(
            self.subject._device, {SPEED_DPS: "high"}
        ):
            await self.subject.async_set_percentage(70)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Manual", "Auto", "Sleep"],
        )

    def test_preset_mode(self):
        self.dps[MODE_DPS] = "manual"
        self.assertEqual(self.subject.preset_mode, "Manual")
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Auto")
        self.dps[MODE_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "Sleep")

    async def test_set_preset_to_manual(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "manual"},
        ):
            await self.subject.async_set_preset_mode("Manual")

    async def test_set_preset_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("Auto")

    async def test_set_preset_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("Sleep")
