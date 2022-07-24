from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

from ..const import BECOOL_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
UNKNOWN4_DPS = "4"
MODE_DPS = "5"
TEMPERATURE_DPS = "6"
FAN_DPS = "8"
UNIT_DPS = "10"
UNKNOWN13_DPS = "13"
UNKNOWN14_DPS = "14"
UNKNOWN15_DPS = "15"
UNKNOWN16_DPS = "16"
UNKNOWN17_DPS = "17"
TEMPF_DPS = "18"
UNKNOWN19_DPS = "19"


class TestBWTHeatpump(
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("becool_heatpump.yaml", BECOOL_HEATPUMP_PAYLOAD)
        self.subject = self.entities["climate"]
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=13,
            max=32,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE),
        )

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = False
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)
        self.dps[UNIT_DPS] = True
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)
        self.dps[HVACMODE_DPS] = True
        self.dps[MODE_DPS] = "0"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[MODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[MODE_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[MODE_DPS] = "3"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)
        self.dps[MODE_DPS] = "4"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
            ],
        )

    async def test_turn_on_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, MODE_DPS: "0"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def test_turn_on_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, MODE_DPS: "1"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_turn_on_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, MODE_DPS: "2"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_on_to_dry(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, MODE_DPS: "3"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.DRY)

    async def test_turn_on_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, MODE_DPS: "4"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.FAN_ONLY)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_fan_modes(self):
        self.assertCountEqual(self.subject.fan_modes, ["low", "medium", "high"])
