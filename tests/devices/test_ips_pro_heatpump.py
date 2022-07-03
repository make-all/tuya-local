from homeassistant.components.climate.const import HVACMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from ..const import IPS_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
HVACMODE_DPS = "105"
UNITS_DPS = "103"
POWERLEVEL_DPS = "104"
TEMPERATURE_DPS = "106"
MIN_TEMPERATUR_DPS = "107"
MAX_TEMPERATUR_DPS = "108"
UNKNOWN115_DPS = "115"
UNKNOWN116_DPS = "116"
PRESET_DPS = "2"
# min and max temperature are not static in real model
MAX_TEMPERATUR = 40
MIN_TEMPERATUR = 18


class TestIpsProHeatpump(
    BasicSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("ips_pro_heatpump.yaml", IPS_HEATPUMP_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            MIN_TEMPERATUR,
            MAX_TEMPERATUR,
        )
        self.setUpBasicSensor(
            POWERLEVEL_DPS,
            self.entities.get("sensor_power_level"),
            unit=PERCENTAGE,
            device_class=SensorDeviceClass.POWER_FACTOR,
            state_class="measurement",
        )
        self.mark_secondary(["sensor_power_level"])

    def test_temperature_unit(self):
        self.dps[UNITS_DPS] = False
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)
        self.dps[UNITS_DPS] = True
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

    def test_minimum_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 18
        self.assertEqual(self.subject.min_temp, 18)

    def test_maximum_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 40
        self.assertEqual(self.subject.max_temp, 40)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = "warm"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_current_temperature(self):
        self.assertEqual(self.subject.current_temperature, 10)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "smart"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[HVACMODE_DPS] = "cool"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[HVACMODE_DPS] = "warm"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    async def test_set_hvac_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "cool"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "warm"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "smart"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT_COOL)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "silence"
        self.assertEqual(self.subject.preset_mode, "silence")

        self.dps[PRESET_DPS] = "smart"
        self.assertEqual(self.subject.preset_mode, "smart")

        self.dps[PRESET_DPS] = "booster"
        self.assertEqual(self.subject.preset_mode, "booster")

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["silence", "smart", "booster"])

    async def test_set_preset_mode_to_silent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "silence"},
        ):
            await self.subject.async_set_preset_mode("silence")

    async def test_set_preset_mode_to_smart(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "smart"},
        ):
            await self.subject.async_set_preset_mode("smart")

    async def test_set_preset_mode_to_smart(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "booster"},
        ):
            await self.subject.async_set_preset_mode("booster")

    # Dummy test to allow model without fix range
    async def test_set_target_temperature_fails_outside_valid_range(self):
        self.dps[TEMPERATURE_DPS] = MAX_TEMPERATUR
        self.assertEqual(self.targetTemp.target_temperature, MAX_TEMPERATUR)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN115_DPS] = 3
        self.dps[UNKNOWN116_DPS] = 4
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_115": 3,
                "unknown_116": 4,
            },
        )
