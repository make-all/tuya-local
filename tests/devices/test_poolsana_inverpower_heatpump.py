import asyncio
import pytest
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from ..const import POOLSANA_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
PRESET_DPS = "4"
HVACACTION_DPS = "11"
TEMPERATURE_UNIT_DPS = "13"

PRESET_BOOST = "Boost"
PRESET_ECO = "ECO"
PRESET_SILENT = "Silent"


PRESET_OPTIONS = [PRESET_BOOST, PRESET_SILENT, PRESET_ECO]

HVAC_HEAT = "Heat"
HVAC_COOL = "Cool"
HVAC_MODES = [HVAC_HEAT, HVAC_COOL]
HVAC_OPTIONS_HEAT = ["_".join([p, HVAC_HEAT]) for p in PRESET_OPTIONS]
HVAC_OPTIONS_COOL = ["_".join([p, HVAC_COOL]) for p in PRESET_OPTIONS]
HVAC_OPTIONS = HVAC_OPTIONS_HEAT + HVAC_OPTIONS_COOL


class TestPoolsanaInverpower9Heatpump(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "poolsana_inverpower_heatpump.yaml", POOLSANA_HEATPUMP_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=20,
            max=40,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
            ),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACACTION_DPS] = "idle"
        self.assertEqual(self.subject.icon, "mdi:hvac")
        self.dps[HVACACTION_DPS] = "cooling"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACACTION_DPS] = "heating"
        self.assertEqual(self.subject.icon, "mdi:hot-tub")

    def test_temperature_unit(self):
        self.dps[TEMPERATURE_UNIT_DPS] = "c"
        self.assertEqual(
            self.subject.temperature_unit,
            TEMP_CELSIUS,
        )
        self.dps[TEMPERATURE_UNIT_DPS] = "f"
        self.assertEqual(
            self.subject.temperature_unit,
            TEMP_FAHRENHEIT,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 28
        self.assertEqual(self.subject.current_temperature, 28)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "Boost_Heat"
        for dps_values, hvac_mode in [
            (HVAC_OPTIONS_HEAT, HVACMode.HEAT),
            (HVAC_OPTIONS_COOL, HVACMode.COOL),
        ]:
            for dps_val in dps_values:
                self.dps[HVACMODE_DPS] = dps_val
                self.assertEqual(
                    self.subject.hvac_mode,
                    hvac_mode,
                )

        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.HEAT,
                HVACMode.COOL,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: next(x for x in HVAC_OPTIONS)},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, PRESET_OPTIONS)

    def test_preset_mode(self):
        for mode in HVAC_MODES:
            for preset in PRESET_OPTIONS:
                self.dps[PRESET_DPS] = "_".join([preset, mode])
                self.assertEqual(self.subject.preset_mode, preset)

    async def _set_preset(self, preset, mode):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "_".join([preset, mode])},
        ):
            await self.subject.async_set_preset_mode(preset)

    async def test_set_preset_boost_cool(self):

        self._set_preset(PRESET_BOOST, HVAC_COOL)

    async def test_set_preset_boost_heat(self):

        self._set_preset(PRESET_BOOST, HVAC_HEAT)

    async def test_set_preset_silent_cool(self):

        self._set_preset(PRESET_SILENT, HVAC_COOL)

    async def test_set_preset_silent_heat(self):

        self._set_preset(PRESET_SILENT, HVAC_HEAT)

    async def test_set_eco_silent_cool(self):

        self._set_preset(PRESET_ECO, HVAC_COOL)

    async def test_set_preset_eco_heat(self):

        self._set_preset(PRESET_ECO, HVAC_HEAT)
