from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import ECOSTRAD_ACCENTIQ_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.number import BasicNumberTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
TIMER_DPS = "10"
UNIT_DPS = "101"


class TestEcostradAccentIqHeater(
    BasicNumberTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "ecostrad_accentiq_heater.yaml",
            ECOSTRAD_ACCENTIQ_HEATER_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS, self.subject, min=0.0, max=45.0, scale=10, step=5
        )
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=12,
            unit=UnitOfTime.HOURS,
        )
        self.mark_secondary(["number_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE,
        )

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = True
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)
        self.dps[UNIT_DPS] = False
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 250
        self.assertEqual(self.subject.current_temperature, 25.0)

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

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})
