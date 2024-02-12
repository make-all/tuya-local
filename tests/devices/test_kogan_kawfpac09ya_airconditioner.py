from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature

from ..const import KOGAN_KAWFPAC09YA_AIRCON_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
FAN_DPS = "5"
UNIT_DPS = "19"
COUNTDOWN_DPS = "105"
UNKNOWN106_DPS = "106"
UNKNOWN107_DPS = "107"


class TestKoganKAWFPAC09YA(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "kogan_kawfpac09ya_airconditioner.yaml",
            KOGAN_KAWFPAC09YA_AIRCON_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16.0,
            max=30.0,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "COOL"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "DRY"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "FAN"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

    def test_minimum_target_temperature_f(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.min_temp, 60)

    def test_maximum_target_temperature_f(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.max_temp, 86)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "COOL"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

        self.dps[HVACMODE_DPS] = "DRY"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)

        self.dps[HVACMODE_DPS] = "FAN"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

        self.dps[HVACMODE_DPS] = "FAN"
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "COOL"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "1"
        self.assertEqual(self.subject.fan_mode, "low")
        self.dps[FAN_DPS] = "2"
        self.assertEqual(self.subject.fan_mode, "high")

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            [
                "low",
                "high",
            ],
        )

    async def test_set_fan_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "1"},
        ):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "2"},
        ):
            await self.subject.async_set_fan_mode("high")

    def test_extra_state_attributes(self):
        self.dps[COUNTDOWN_DPS] = 105
        self.dps[UNKNOWN106_DPS] = 106
        self.dps[UNKNOWN107_DPS] = True
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "countdown": 105,
                "unknown_106": 106,
                "unknown_107": True,
            },
        )
