from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.components.humidifier.const import (
    MODE_AUTO,
    MODE_BOOST,
    MODE_NORMAL,
    MODE_SLEEP,
)
from homeassistant.const import PERCENTAGE

from ..const import WETAIR_WAWH1210_HUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.lock import BasicLockTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
LIGHT_DPS = "5"
SOUND_DPS = "8"
HUMIDITY_DPS = "13"
CURRENTHUMID_DPS = "14"
UNKNOWN22_DPS = "22"
PRESET_DPS = "24"
IONIZER_DPS = "25"
LOCK_DPS = "29"
LEVEL_DPS = "101"


class TestWetairWAWH1210LWHumidifier(
    BasicLightTests,
    BasicLockTests,
    MultiSensorTests,
    MultiSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "wetair_wawh1210lw_humidifier.yaml", WETAIR_WAWH1210_HUMIDIFIER_PAYLOAD
        )
        self.subject = self.entities.get("humidifier_humidifier")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpMultiSensors(
            [
                {
                    "dps": LEVEL_DPS,
                    "name": "sensor_water_level",
                    "unit": PERCENTAGE,
                },
            ]
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": SOUND_DPS,
                    "name": "switch_sound",
                },
                {
                    "dps": IONIZER_DPS,
                    "name": "switch_ionizer",
                },
            ]
        )
        self.mark_secondary(
            [
                "light_display",
                "lock_child_lock",
                "sensor_water_level",
                "switch_sound",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, HumidifierEntityFeature.MODES)

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    def test_available_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            [MODE_AUTO, MODE_BOOST, MODE_NORMAL, MODE_SLEEP],
        )

    def test_mode(self):
        self.dps[PRESET_DPS] = "AUTO"
        self.assertEqual(self.subject.mode, MODE_AUTO)
        self.dps[PRESET_DPS] = "MIDDLE"
        self.assertEqual(self.subject.mode, MODE_NORMAL)
        self.dps[PRESET_DPS] = "HIGH"
        self.assertEqual(self.subject.mode, MODE_BOOST)
        self.dps[PRESET_DPS] = "SLEEP"
        self.assertEqual(self.subject.mode, MODE_SLEEP)

    async def test_set_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "AUTO"}
        ):
            await self.subject.async_set_mode(MODE_AUTO)

    async def test_set_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "MIDDLE"}
        ):
            await self.subject.async_set_mode(MODE_NORMAL)

    async def test_set_mode_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "HIGH"}
        ):
            await self.subject.async_set_mode(MODE_BOOST)

    async def test_set_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "SLEEP"}
        ):
            await self.subject.async_set_mode(MODE_SLEEP)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN22_DPS] = 22
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"unknown_22": 22},
        )
