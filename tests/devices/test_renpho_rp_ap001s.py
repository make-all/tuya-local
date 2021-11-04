from homeassistant.components.fan import SUPPORT_PRESET_MODE
from homeassistant.components.light import COLOR_MODE_ONOFF
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..const import RENPHO_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import (
    BasicLightTests,
    BasicLockTests,
    BasicSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
)

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


class TestRenphoPurifier(
    BasicLightTests,
    BasicLockTests,
    BasicSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("renpho_rp_ap001s.yaml", RENPHO_PURIFIER_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_aq_indicator"))
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSwitch(SLEEP_DPS, self.entities.get("switch_sleep"))

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_PRESET_MODE)

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

        self.assertEqual(self.basicSwitch.icon, "mdi:power-sleep")
