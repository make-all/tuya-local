from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import TEMP_CELSIUS

from ..const import WEAU_POOL_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
UNKNOWN6_DPS = "6"


class TestWeauPoolHeatpump(
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

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 194
        self.assertEqual(self.subject.current_temperature, 19.4)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT_COOL)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_HEAT_COOL],
        )

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    async def test_set_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "cold"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_COOL)

    async def test_set_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "hot"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_set_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "auto"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT_COOL)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN6_DPS] = 6
        self.assertDictEqual(self.subject.extra_state_attributes, {"unknown_6": 6})
