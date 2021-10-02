from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    FAN_AUTO,
    FAN_ON,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_FAN_MODE,
)
from homeassistant.const import STATE_UNAVAILABLE, TEMP_CELSIUS, TEMP_FAHRENHEIT
from unittest.mock import ANY

from ..const import SASWELL_T29UTK_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACACTION_DPS = "4"
FAN_DPS = "5"
UNITS_DPS = "19"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"
HVACMODE_DPS = "103"
UNKNOWN112_DPS = "112"
UNKNOWN113_DPS = "113"
TEMPC_DPS = "114"
CURTEMPC_DPS = "115"
TEMPF_DPS = "116"
CURTEMPF_DPS = "117"


class TestSaswellT29UTKThermostat(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "saswell_t29utk_thermostat.yaml", SASWELL_T29UTK_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE,
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACACTION_DPS] = "cold"
        self.assertEqual(self.subject.icon, "mdi:thermometer-minus")

        self.dps[HVACACTION_DPS] = "heat"
        self.assertEqual(self.subject.icon, "mdi:thermometer-plus")

        self.dps[HVACACTION_DPS] = "off"
        self.assertEqual(self.subject.icon, "mdi:thermometer")

        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:thermometer-off")

    def test_temperature_unit(self):
        self.dps[UNITS_DPS] = "c"
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

        self.dps[UNITS_DPS] = "f"
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 250
        self.assertEqual(self.subject.target_temperature, 25.0)

    def test_target_temperature_step(self):
        self.dps[UNITS_DPS] = "c"
        self.assertEqual(self.subject.target_temperature_step, 0.5)
        self.dps[UNITS_DPS] = "f"
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_set_target_temperature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 245},
        ):
            await self.subject.async_set_target_temperature(24.5)

    async def test_set_target_temperature_rounds_value_to_half_degrees(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 245},
        ):
            await self.subject.async_set_target_temperature(24.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(4\\) must be between 5.0 and 35.0"
        ):
            await self.subject.async_set_target_temperature(4)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 250
        self.assertEqual(self.subject.current_temperature, 25.0)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = False
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[POWER_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)

        self.dps[HVACMODE_DPS] = "heat"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF],
        )

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False, HVACMODE_DPS: ANY}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    async def test_set_hvac_mode_cool(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "cold"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_COOL)

    async def test_set_hvac_mode_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "heat"}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    def test_hvac_action(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACACTION_DPS] = "cold"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_COOL)

        self.dps[HVACACTION_DPS] = "heat"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_HEAT)
        self.dps[HVACACTION_DPS] = "off"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_IDLE)

        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_OFF)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "auto"
        self.assertEqual(self.subject.fan_mode, FAN_AUTO)
        self.dps[FAN_DPS] = "on"
        self.assertEqual(self.subject.fan_mode, FAN_ON)

    def test_fan_modes(self):
        self.assertCountEqual(self.subject.fan_modes, [FAN_AUTO, FAN_ON])

    async def test_set_fan_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "on"},
        ):
            await self.subject.async_set_fan_mode(FAN_ON)

    async def test_set_fan_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "auto"},
        ):
            await self.subject.async_set_fan_mode(FAN_AUTO)

    def test_device_state_attributes(self):
        self.dps[UNKNOWN101_DPS] = True
        self.dps[UNKNOWN102_DPS] = False
        self.dps[UNKNOWN112_DPS] = "unknown112"
        self.dps[UNKNOWN113_DPS] = 113
        self.dps[TEMPC_DPS] = 114
        self.dps[CURTEMPC_DPS] = 115
        self.dps[TEMPF_DPS] = 116
        self.dps[CURTEMPF_DPS] = 117

        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "unknown_101": True,
                "unknown_102": False,
                "unknown_112": "unknown112",
                "unknown_113": 113,
                "temperature_c": 114,
                "current_temperature_c": 115,
                "temperature_f": 116,
                "current_temperature_f": 117,
            },
        )
