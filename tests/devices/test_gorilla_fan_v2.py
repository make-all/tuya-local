from homeassistant.components.fan import FanEntityFeature

from ..const import FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
PRESET_DPS = "2"
FANMODE_DPS = "3"

class TestGorillaFanV2(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("gorilla_fan_v2.yaml", FAN_PAYLOAD)
        self.subject = self.entities.get("fan")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                FanEntityFeature.PRESET_MODE
                | FanEntityFeature.SET_SPEED
            ),
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.subject.preset_mode, "Normal")

        self.dps[PRESET_DPS] = "boost"
        self.assertEqual(self.subject.preset_mode, "Boost")

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["normal", "boost"])

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("Normal")

    async def test_set_preset_mode_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "boost"},
        ):
            await self.subject.async_set_preset_mode("Boost")

    def test_speed(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[FANMODE_DPS] = 3
        self.assertEqual(self.subject.percentage, 60)

    async def test_set_speed_in_normal_mode(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 3}):
            await self.subject.async_set_percentage(60)

    async def test_set_speed_in_boost_mode(self):
        self.dps[PRESET_DPS] = "boost"
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 5}):
            await self.subject.async_set_percentage(100)

    async def test_set_speed_to_zero_turns_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_set_percentage(0)

