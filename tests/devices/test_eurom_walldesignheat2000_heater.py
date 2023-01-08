from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.const import UnitOfTemperature

from ..const import EUROM_WALLDESIGNHEAT2000_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
SWING_DPS = "7"


class TestEuromWallDesignheat2000Heater(
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "eurom_walldesignheat2000_heater.yaml",
            EUROM_WALLDESIGNHEAT2000_HEATER_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=10,
            max=35,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.SWING_MODE
            ),
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")
        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:radiator")
        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.icon, "mdi:fan")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = "100_perc"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY],
        )

    async def test_set_hvac_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, PRESET_DPS: "auto"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, PRESET_DPS: "off"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.FAN_ONLY)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [PRESET_BOOST, PRESET_COMFORT, PRESET_ECO, "fan"],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.preset_mode, "fan")
        self.dps[PRESET_DPS] = "50_perc"
        self.assertEqual(self.subject.preset_mode, PRESET_ECO)
        self.dps[PRESET_DPS] = "100_perc"
        self.assertEqual(self.subject.preset_mode, PRESET_BOOST)
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, PRESET_COMFORT)

    async def test_set_preset_more_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "50_perc"}
        ):
            await self.subject.async_set_preset_mode(PRESET_ECO)

    async def test_set_preset_more_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "100_perc"}
        ):
            await self.subject.async_set_preset_mode(PRESET_BOOST)

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "auto"}
        ):
            await self.subject.async_set_preset_mode(PRESET_COMFORT)

    async def test_set_preset_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "off"}
        ):
            await self.subject.async_set_preset_mode("fan")

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            [SWING_OFF, SWING_VERTICAL],
        )

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, SWING_VERTICAL)

    async def test_set_swing_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode(SWING_VERTICAL)

    async def test_set_swing_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode(SWING_OFF)

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})
