from homeassistant.components.fan import FanEntityFeature
from homeassistant.const import UnitOfTime

from ..const import ANKO_FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import BasicNumberTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
PRESET_DPS = "2"
SPEED_DPS = "3"
OSCILLATE_DPS = "4"
TIMER_DPS = "6"


class TestAnkoFan(SwitchableTests, BasicNumberTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("anko_fan.yaml", ANKO_FAN_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=9,
            unit=UnitOfTime.HOURS,
        )
        self.mark_secondary(["number_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            FanEntityFeature.OSCILLATE
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF,
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "sleep")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["normal", "nature", "sleep"])

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_nature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "nature"},
        ):
            await self.subject.async_set_preset_mode("nature")

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    def test_oscillating(self):
        self.dps[OSCILLATE_DPS] = "off"
        self.assertFalse(self.subject.oscillating)

        self.dps[OSCILLATE_DPS] = "auto"
        self.assertTrue(self.subject.oscillating)

        self.dps[OSCILLATE_DPS] = None
        self.assertFalse(self.subject.oscillating)

    async def test_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device, {OSCILLATE_DPS: "off"}
        ):
            await self.subject.async_oscillate(False)

    async def test_oscillate_on(self):
        async with assert_device_properties_set(
            self.subject._device, {OSCILLATE_DPS: "auto"}
        ):
            await self.subject.async_oscillate(True)

    def test_speed(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[SPEED_DPS] = "4"
        self.assertEqual(self.subject.percentage, 50)

    def test_speed_step(self):
        self.assertEqual(self.subject.percentage_step, 12.5)
        self.assertEqual(self.subject.speed_count, 8)

    async def test_set_speed_in_normal_mode(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: "2"}):
            await self.subject.async_set_percentage(25)

    async def test_set_speed_in_normal_mode_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: "6"}):
            await self.subject.async_set_percentage(80)

    async def test_turn_on_with_params(self):
        self.dps[SWITCH_DPS] = False
        self.dps[SPEED_DPS] = "1"
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True, SPEED_DPS: "6", PRESET_DPS: "nature"},
        ):
            await self.subject.async_turn_on(80, "nature")
