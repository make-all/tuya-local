from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature

from ..const import EUROM_600_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "5"
ERROR_DPS = "6"


class TestEurom600Heater(
    BasicBinarySensorTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("eurom_600_heater.yaml", EUROM_600_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=0.0,
            max=37.0,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["binary_sensor_problem"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON,
        )

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

    def test_basic_bsensor_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 2
        self.assertEqual(self.basicBSensor.extra_state_attributes, {"fault_code": 2})
