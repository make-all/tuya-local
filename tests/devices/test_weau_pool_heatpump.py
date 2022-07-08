from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from ..const import WEAU_POOL_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
MODE_DPS = "4"
FAULT_DPS = "6"


class TestWeauPoolHeatpump(
    BasicBinarySensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("weau_pool_heatpump.yaml", WEAU_POOL_HEATPUMP_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=7,
            max=60,
        )
        self.setUpBasicBinarySensor(
            FAULT_DPS,
            self.entities.get("binary_sensor_fault"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(4, 0),
        )
        self.mark_secondary(["binary_sensor_fault"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 194
        self.assertEqual(self.subject.current_temperature, 19.4)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[MODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[MODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[MODE_DPS] = "eco"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.HEAT_COOL],
        )

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    async def test_set_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, MODE_DPS: "cold"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, MODE_DPS: "eco"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, MODE_DPS: "auto"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT_COOL)

    def test_preset_mode(self):
        self.dps[MODE_DPS] = "eco"
        self.assertEqual(self.subject.preset_mode, "Eco Heat")
        self.dps[MODE_DPS] = "hot"
        self.assertEqual(self.subject.preset_mode, "Boost Heat")
        self.dps[MODE_DPS] = "cold"
        self.assertEqual(self.subject.preset_mode, "Cool")
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Auto")

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Eco Heat", "Boost Heat", "Cool", "Auto"],
        )

    async def test_set_preset_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "hot"},
        ):
            await self.subject.async_set_preset_mode("Boost Heat")

    async def test_set_preset_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "eco"},
        ):
            await self.subject.async_set_preset_mode("Eco Heat")

    def test_extra_state_attributes(self):
        self.dps[FAULT_DPS] = 6
        self.assertDictEqual(self.subject.extra_state_attributes, {"fault": 6})
