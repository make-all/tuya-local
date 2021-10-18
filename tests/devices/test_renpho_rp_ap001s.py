from homeassistant.components.fan import SUPPORT_PRESET_MODE
from homeassistant.components.light import COLOR_MODE_ONOFF
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..const import RENPHO_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
PRESET_DPS = "4"
LOCK_DPS = "7"
LIGHT_DPS = "8"
TIMER_DPS = "19"
QUALITY_DPS = "22"
SLEEP_DPS = "101"
PREFILTER_DPS = "102"
CHARCOAL_DPS = "103"
ACTIVATED_DPS = "104"
HEPA_DPS = "105"


class TestRenphoPurifier(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("renpho_rp_ap001s.yaml", RENPHO_PURIFIER_PAYLOAD)
        self.subject = self.entities["fan"]
        self.light = self.entities["light_aq_indicator"]
        self.lock = self.entities["lock_child_lock"]
        self.switch = self.entities["switch_sleep"]

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_PRESET_MODE)

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)
        self.dps[SWITCH_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True},
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: False},
        ):
            await self.subject.async_turn_off()

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["low", "mid", "high", "auto"],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "low"
        self.assertEqual(self.subject.preset_mode, "low")
        self.dps[PRESET_DPS] = "mid"
        self.assertEqual(self.subject.preset_mode, "mid")
        self.dps[PRESET_DPS] = "high"
        self.assertEqual(self.subject.preset_mode, "high")
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "auto")

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "low"},
        ):
            await self.subject.async_set_preset_mode("low")

    async def test_set_preset_mode_to_mid(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mid"},
        ):
            await self.subject.async_set_preset_mode("mid")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "high"},
        ):
            await self.subject.async_set_preset_mode("high")

    async def test_set_preset_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("auto")

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "19"
        self.dps[QUALITY_DPS] = "22"
        self.dps[PREFILTER_DPS] = 102
        self.dps[CHARCOAL_DPS] = 103
        self.dps[ACTIVATED_DPS] = 104
        self.dps[HEPA_DPS] = 105

        self.assertDictEqual(
            self.subject.device_state_attributes,
            {
                "timer": "19",
                "air_quality": "22",
                "prefilter_life": 102,
                "charcoal_filter_life": 103,
                "activated_charcoal_filter_life": 104,
                "hepa_filter_life": 105,
            },
        )

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
        async with assert_device_properties_set(
            self.lock._device,
            {LOCK_DPS: True},
        ):
            await self.lock.async_lock()

    async def test_lock_unlocks(self):
        async with assert_device_properties_set(
            self.lock._device,
            {LOCK_DPS: False},
        ):
            await self.lock.async_unlock()

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, COLOR_MODE_ONOFF)

    def test_light_has_no_brightness(self):
        self.assertIsNone(self.light.brightness)

    def test_light_icon(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-off")

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.is_on, True)

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.is_on, False)

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

    def test_switch_icon(self):
        self.assertEqual(self.switch.icon, "mdi:power-sleep")

    def test_switch_is_on(self):
        self.dps[SLEEP_DPS] = True
        self.assertEqual(self.switch.is_on, True)

        self.dps[SLEEP_DPS] = False
        self.assertEqual(self.switch.is_on, False)

    def test_switch_state_attributes(self):
        self.assertEqual(self.switch.device_state_attributes, {})

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(self.switch._device, {SLEEP_DPS: True}):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.switch._device, {SLEEP_DPS: False}
        ):
            await self.switch.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[SLEEP_DPS] = False

        async with assert_device_properties_set(self.switch._device, {SLEEP_DPS: True}):
            await self.switch.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[SLEEP_DPS] = True

        async with assert_device_properties_set(
            self.switch._device, {SLEEP_DPS: False}
        ):
            await self.switch.async_toggle()
