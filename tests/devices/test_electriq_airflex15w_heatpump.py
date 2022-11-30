from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from ..const import ELECTRIQ_AIRFLEX15W_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HUMIDITY_DPS = "17"
UNKNOWN20_DPS = "20"
HVACMODE_DPS = "101"
UNKNOWN103_DPS = "103"
FAN_DPS = "104"
UNKNOWN105_DPS = "105"
UNKNOWN106_DPS = "106"
UNIT_DPS = "109"
TEMPF_DPS = "110"
CURTEMPF_DPS = "111"
CURHUMID_DPS = "112"


class TestElectriqAirflex15WHeatpump(
    BasicSelectTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "electriq_airflex15w_heatpump.yaml", ELECTRIQ_AIRFLEX15W_PAYLOAD
        )
        self.subject = self.entities.get("climate")

        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16,
            max=31,
        )
        self.setUpBasicSelect(
            UNIT_DPS,
            self.entities.get("select_temperature_unit"),
            {
                False: "Celsius",
                True: "Fahrenheit",
            },
        )
        self.mark_secondary(["select_temperature_unit"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TARGET_HUMIDITY
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.PRESET_MODE
            ),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "0"
        self.assertEqual(self.subject.icon, "mdi:hvac")
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "3"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "5"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = False
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)
        self.dps[UNIT_DPS] = True
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

    def test_current_temperature(self):
        self.dps[UNIT_DPS] = False
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)
        self.dps[UNIT_DPS] = True
        self.dps[CURTEMPF_DPS] = 78
        self.assertEqual(self.subject.current_temperature, 78)

    def test_temperature_f(self):
        self.dps[UNIT_DPS] = True
        self.dps[TEMPF_DPS] = 90
        self.assertEqual(self.subject.target_temperature, 90)

    async def test_set_temperature_f(self):
        self.dps[UNIT_DPS] = True
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPF_DPS: 85},
        ):
            await self.subject.async_set_temperature(temperature=85)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[HVACMODE_DPS] = "3"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)
        self.dps[HVACMODE_DPS] = "0"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[HVACMODE_DPS] = "5"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "2"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "1"
        self.assertEqual(self.subject.fan_mode, "high")
        self.dps[FAN_DPS] = "2"
        self.assertEqual(self.subject.fan_mode, "medium")
        self.dps[FAN_DPS] = "3"
        self.assertEqual(self.subject.fan_mode, "low")

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            [
                "high",
                "medium",
                "low",
            ],
        )

    async def test_set_fan_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "1"},
        ):
            await self.subject.async_set_fan_mode("high")

    async def test_set_fan_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "2"},
        ):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "3"},
        ):
            await self.subject.async_set_fan_mode("low")

    def test_humidity(self):
        self.dps[HUMIDITY_DPS] = 74
        self.assertEqual(self.subject.target_humidity, 74)

    async def test_set_humidity(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 40},
        ):
            await self.subject.async_set_humidity(40)

    def test_extra_state_attribures(self):
        self.dps[UNKNOWN20_DPS] = 20
        self.dps[UNKNOWN103_DPS] = True
        self.dps[UNKNOWN105_DPS] = 105
        self.dps[UNKNOWN106_DPS] = True
        self.assertEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_20": 20,
                "unknown_103": True,
                "unknown_105": 105,
                "unknown_106": True,
            },
        )
