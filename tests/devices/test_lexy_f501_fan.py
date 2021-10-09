from homeassistant.components.fan import (
    SUPPORT_OSCILLATE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
)
from homeassistant.components.light import COLOR_MODE_ONOFF
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..const import LEXY_F501_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
PRESET_DPS = "2"
OSCILLATE_DPS = "4"
TIMER_DPS = "6"
LIGHT_DPS = "9"
LOCK_DPS = "16"
SWITCH_DPS = "17"
SPEED_DPS = "102"


class TestLexyF501Fan(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("lexy_f501_fan.yaml", LEXY_F501_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.light = self.entities.get("light")
        self.lock = self.entities.get("lock")
        self.switch = self.entities.get("switch")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_OSCILLATE | SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED,
        )

    def test_is_on(self):
        self.dps[POWER_DPS] = True
        self.assertTrue(self.subject.is_on)

        self.dps[POWER_DPS] = False
        self.assertFalse(self.subject.is_on)

        self.dps[POWER_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_turn_off()

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "forestwindhigh"
        self.assertEqual(self.subject.preset_mode, "Forest High")

        self.dps[PRESET_DPS] = "forestwindlow"
        self.assertEqual(self.subject.preset_mode, "Forest Low")

        self.dps[PRESET_DPS] = "sleepwindlow"
        self.assertEqual(self.subject.preset_mode, "Sleep Low")

        self.dps[PRESET_DPS] = "sleepwindhigh"
        self.assertEqual(self.subject.preset_mode, "Sleep High")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Forest High", "Forest Low", "Sleep High", "Sleep Low"],
        )

    async def test_set_preset_mode_to_foresthigh(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "forestwindhigh"},
        ):
            await self.subject.async_set_preset_mode("Forest High")

    async def test_set_preset_mode_to_forestlow(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "forestwindlow"},
        ):
            await self.subject.async_set_preset_mode("Forest Low")

    async def test_set_preset_mode_to_sleephigh(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleepwindhigh"},
        ):
            await self.subject.async_set_preset_mode("Sleep High")

    async def test_set_preset_mode_to_sleeplow(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleepwindlow"},
        ):
            await self.subject.async_set_preset_mode("Sleep Low")

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

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.assertEqual(self.subject.device_state_attributes, {"timer": 5})

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, COLOR_MODE_ONOFF)

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.is_on, True)

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.is_on, False)

    def test_light_state_attributes(self):
        self.assertEqual(self.light.device_state_attributes, {})

    async def test_light_turn_on(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_turn_off()

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[LIGHT_DPS] = False

        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[LIGHT_DPS] = True

        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_toggle()

    def test_switch_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.switch.is_on, True)

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.switch.is_on, False)

    def test_switch_state_attributes(self):
        self.assertEqual(self.switch.device_state_attributes, {})

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: True}
        ):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: False}
        ):
            await self.switch.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[SWITCH_DPS] = False

        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: True}
        ):
            await self.switch.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[SWITCH_DPS] = True

        async with assert_device_properties_set(
            self.switch._device, {SWITCH_DPS: False}
        ):
            await self.switch.async_toggle()

    def test_lock_state(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.lock.state, STATE_LOCKED)

        self.dps[LOCK_DPS] = False
        self.assertEqual(self.lock.state, STATE_UNLOCKED)

        self.dps[LOCK_DPS] = None
        self.assertEqual(self.lock.state, STATE_UNAVAILABLE)

    def test_lock_is_locked(self):
        self.dps[LOCK_DPS] = True
        self.assertTrue(self.lock.is_locked)

        self.dps[LOCK_DPS] = False
        self.assertFalse(self.lock.is_locked)

        self.dps[LOCK_DPS] = None
        self.assertFalse(self.lock.is_locked)

    async def test_lock_locks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: True}):
            await self.lock.async_lock()

    async def test_lock_unlocks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: False}):
            await self.lock.async_unlock()

    def test_icons(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-off")
