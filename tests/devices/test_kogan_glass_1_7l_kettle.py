from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from ..const import KOGAN_GLASS_1_7L_KETTLE_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
CURRENTTEMP_DPS = "5"
# PRESET_DPS = "102"


class TestKoganGlass1_7LKettle(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "kogan_glass_1_7l_kettle.yaml",
            KOGAN_GLASS_1_7L_KETTLE_PAYLOAD,
        )
        self.subject = self.entities.get("climate")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:kettle")
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:kettle-off")

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 85
        self.assertEqual(self.subject.current_temperature, 85)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.HEAT, HVACMode.OFF],
        )

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: True},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    # def test_preset_modes(self):
    #     self.assertCountEqual(
    #         self.subject.preset_modes,
    #         ["40", "50", "60", "80", "90", "Current Temp"],
    #     )

    # def test_preset_mode(self):
    #     self.dps[PRESET_DPS] = "40"
    #     self.assertEqual(self.subject.preset_mode, "40")
    #     self.dps[PRESET_DPS] = "50"
    #     self.assertEqual(self.subject.preset_mode, "50")
    #     self.dps[PRESET_DPS] = "60"
    #     self.assertEqual(self.subject.preset_mode, "60")
    #     self.dps[PRESET_DPS] = "80"
    #     self.assertEqual(self.subject.preset_mode, "80")
    #     self.dps[PRESET_DPS] = "90"
    #     self.assertEqual(self.subject.preset_mode, "90")
    #     self.dps[PRESET_DPS] = "currenttemp"
    #     self.assertEqual(self.subject.preset_mode, "Current Temp")

    # async def test_set_preset_to_40(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {PRESET_DPS: "40"},
    #     ):
    #         await self.subject.async_set_preset_mode("40")

    # async def test_set_preset_to_50(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {PRESET_DPS: "50"},
    #     ):
    #         await self.subject.async_set_preset_mode("50")

    # async def test_set_preset_to_60(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {PRESET_DPS: "60"},
    #     ):
    #         await self.subject.async_set_preset_mode("60")

    # async def test_set_preset_to_80(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {PRESET_DPS: "80"},
    #     ):
    #         await self.subject.async_set_preset_mode("80")

    # async def test_set_preset_to_90(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {PRESET_DPS: "90"},
    #     ):
    #         await self.subject.async_set_preset_mode("90")

    # async def test_set_preset_to_currenttemp(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {PRESET_DPS: "currenttemp"},
    #     ):
    #         await self.subject.async_set_preset_mode("Current Temp")
