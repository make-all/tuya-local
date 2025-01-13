from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass

from ..const import RENPHO_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.lock import BasicLockTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
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


class TestRenphoPurifier(
    BasicLightTests,
    BasicLockTests,
    BasicSwitchTests,
    MultiSensorTests,
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
        self.setUpBasicSwitch(
            SLEEP_DPS,
            self.entities.get("switch_sleep"),
            device_class=SwitchDeviceClass.SWITCH,
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_air_quality",
                    "dps": QUALITY_DPS,
                    "device_class": SensorDeviceClass.ENUM,
                    "options": ["poor", "moderate", "good"],
                },
                {
                    "name": "sensor_prefilter_life",
                    "dps": PREFILTER_DPS,
                },
                {
                    "name": "sensor_charcoal_filter_life",
                    "dps": CHARCOAL_DPS,
                },
                {
                    "name": "sensor_active_filter_life",
                    "dps": ACTIVATED_DPS,
                },
                {
                    "name": "sensor_hepa_filter_life",
                    "dps": HEPA_DPS,
                },
            ]
        )
        self.mark_secondary(
            [
                "light_aq_indicator",
                "lock_child_lock",
                "sensor_air_quality",
                "sensor_active_filter_life",
                "sensor_charcoal_filter_life",
                "sensor_hepa_filter_life",
                "sensor_prefilter_life",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON,
        )

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["sleep", "fresh", "strong", "smart"],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "low"
        self.assertEqual(self.subject.preset_mode, "sleep")
        self.dps[PRESET_DPS] = "mid"
        self.assertEqual(self.subject.preset_mode, "fresh")
        self.dps[PRESET_DPS] = "high"
        self.assertEqual(self.subject.preset_mode, "strong")
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "smart")

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "low"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    async def test_set_preset_mode_to_mid(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mid"},
        ):
            await self.subject.async_set_preset_mode("fresh")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "high"},
        ):
            await self.subject.async_set_preset_mode("strong")

    async def test_set_preset_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("smart")

    def test_extra_state_attributes(self):
        self.dps[TIMER_DPS] = "19"

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "timer": "19",
            },
        )
