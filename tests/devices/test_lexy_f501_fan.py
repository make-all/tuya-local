from homeassistant.components.fan import FanEntityFeature
from homeassistant.const import UnitOfTime

from ..const import LEXY_F501_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
PRESET_DPS = "2"
OSCILLATE_DPS = "4"
TIMER_DPS = "6"
LIGHT_DPS = "9"
LOCK_DPS = "16"
SWITCH_DPS = "17"
SPEED_DPS = "102"


class TestLexyF501Fan(
    SwitchableTests,
    BasicLightTests,
    BasicLockTests,
    BasicNumberTests,
    BasicSwitchTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("lexy_f501_fan.yaml", LEXY_F501_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.setUpSwitchable(POWER_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light"))
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=7,
            unit=UnitOfTime.HOURS,
        )
        self.setUpBasicSwitch(SWITCH_DPS, self.entities.get("switch_sound"))
        self.mark_secondary(
            [
                "light",
                "lock_child_lock",
                "number_timer",
                "switch_sound",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                FanEntityFeature.OSCILLATE
                | FanEntityFeature.PRESET_MODE
                | FanEntityFeature.SET_SPEED
            ),
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "forestwindhigh"
        self.assertEqual(self.subject.preset_mode, "strong")

        self.dps[PRESET_DPS] = "forestwindlow"
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleepwindlow"
        self.assertEqual(self.subject.preset_mode, "sleep")

        self.dps[PRESET_DPS] = "sleepwindhigh"
        self.assertEqual(self.subject.preset_mode, "fresh")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["strong", "nature", "fresh", "sleep"],
        )

    async def test_set_preset_mode_to_foresthigh(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "forestwindhigh"},
        ):
            await self.subject.async_set_preset_mode("strong")

    async def test_set_preset_mode_to_forestlow(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "forestwindlow"},
        ):
            await self.subject.async_set_preset_mode("nature")

    async def test_set_preset_mode_to_sleephigh(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleepwindhigh"},
        ):
            await self.subject.async_set_preset_mode("fresh")

    async def test_set_preset_mode_to_sleeplow(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleepwindlow"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    def test_oscillating(self):
        self.dps[OSCILLATE_DPS] = "off"
        self.assertFalse(self.subject.oscillating)

        self.dps[OSCILLATE_DPS] = "30"
        self.assertTrue(self.subject.oscillating)
        self.dps[OSCILLATE_DPS] = "60"
        self.assertTrue(self.subject.oscillating)
        self.dps[OSCILLATE_DPS] = "90"
        self.assertTrue(self.subject.oscillating)
        self.dps[OSCILLATE_DPS] = "360positive"
        self.assertTrue(self.subject.oscillating)
        self.dps[OSCILLATE_DPS] = "360negative"
        self.assertTrue(self.subject.oscillating)

        self.dps[OSCILLATE_DPS] = None
        self.assertFalse(self.subject.oscillating)

    async def test_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device, {OSCILLATE_DPS: "off"}
        ):
            await self.subject.async_oscillate(False)

    def test_speed(self):
        self.dps[SPEED_DPS] = "6"
        self.assertEqual(self.subject.percentage, 40)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 6.7, 1)
        self.assertEqual(self.subject.speed_count, 15)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 3}):
            await self.subject.async_set_percentage(20)

    async def test_set_speed_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 12}):
            await self.subject.async_set_percentage(78)

    def test_extra_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.assertEqual(self.subject.extra_state_attributes, {"timer": 5})

    def test_icons(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")
