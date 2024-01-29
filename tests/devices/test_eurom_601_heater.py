from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature

from ..const import EUROM_601_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "6"
ERROR_DPS = "13"


class TestEurom601Heater(
    BasicBinarySensorTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("eurom_601_heater.yaml", EUROM_601_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=0,
            max=37,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["binary_sensor_error"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
            ),
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [PRESET_COMFORT, PRESET_ECO],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = True
        self.assertEqual(self.subject.preset_mode, PRESET_ECO)

        self.dps[PRESET_DPS] = False
        self.assertEqual(self.subject.preset_mode, PRESET_COMFORT)

    async def test_set_preset_more_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: True}
        ):
            await self.subject.async_set_preset_mode(PRESET_ECO)

    async def test_set_preset_more_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: False}
        ):
            await self.subject.async_set_preset_mode(PRESET_COMFORT)

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 13
        self.assertCountEqual(
            self.subject.extra_state_attributes,
            {"error": 13},
        )
