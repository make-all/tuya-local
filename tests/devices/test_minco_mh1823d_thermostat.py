from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

from ..const import MINCO_MH1823D_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
PRESET_DPS = "2"
HVACACTION_DPS = "3"
LOCK_DPS = "5"
ANTIFROST_DPS = "9"
UNKNOWN12_DPS = "12"
SELECT_DPS = "18"
UNIT_DPS = "19"
TEMPERATURE_DPS = "22"
TEMPF_DPS = "23"
UNKNOWN32_DPS = "32"
CURRENTTEMP_DPS = "33"
CALIBINT_DPS = "35"
CURTEMPF_DPS = "37"
SCHEDULE_DPS = "39"
UNKNOWN45_DPS = "45"
EXTERNTEMP_DPS = "101"
EXTTEMPF_DPS = "102"
CALIBEXT_DPS = "103"
CALIBSWING_DPS = "104"
UNKNOWN105_DPS = "105"
TEMPLIMIT_DPS = "106"
TEMPLIMITF_DPS = "107"


class TestMincoMH1823DThermostat(
    BasicLockTests,
    BasicSensorTests,
    BasicSwitchTests,
    MultiNumberTests,
    MultiSelectTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "minco_mh1823d_thermostat.yaml",
            MINCO_MH1823D_THERMOSTAT_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5,
            max=50,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSensor(
            EXTERNTEMP_DPS,
            self.entities.get("sensor_external_temperature"),
            unit=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class="measurement",
            testdata=(300, 30.0),
        )
        self.setUpBasicSwitch(ANTIFROST_DPS, self.entities.get("switch_anti_frost"))
        self.setUpMultiNumber(
            [
                {
                    "name": "number_calibration_offset_internal",
                    "dps": CALIBINT_DPS,
                    "min": -9,
                    "max": 9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_calibration_offset_external",
                    "dps": CALIBEXT_DPS,
                    "min": -9,
                    "max": 9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_calibration_swing",
                    "dps": CALIBSWING_DPS,
                    "min": 1,
                    "max": 9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_high_temperature_limit",
                    "dps": TEMPLIMIT_DPS,
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 5,
                    "max": 65,
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ]
        )
        self.setUpMultiSelect(
            [
                {
                    "name": "select_temperature_sensor",
                    "dps": SELECT_DPS,
                    "options": {
                        "in": "Internal",
                        "out": "External",
                    },
                },
                {
                    "name": "select_temperature_unit",
                    "dps": UNIT_DPS,
                    "options": {
                        "c": "Celsius",
                        "f": "Fahrenheit",
                    },
                },
                {
                    "name": "select_schedule",
                    "dps": SCHEDULE_DPS,
                    "options": {
                        "7": "7 day",
                        "5_2": "5+2 day",
                        "6_1": "6+1 day",
                    },
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "number_calibration_offset_internal",
                "number_calibration_offset_external",
                "number_calibration_swing",
                "number_high_temperature_limit",
                "select_temperature_sensor",
                "select_temperature_unit",
                "select_schedule",
                "switch_anti_frost",
            ]
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
        self.dps[HVACMODE_DPS] = True
        self.dps[HVACACTION_DPS] = "start"
        self.assertEqual(self.subject.icon, "mdi:thermometer")

        self.dps[HVACACTION_DPS] = "stop"
        self.assertEqual(self.subject.icon, "mdi:thermometer-off")

        self.assertEqual(self.basicSwitch.icon, "mdi:snowflake-melt")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

    def test_target_temperature_f(self):
        self.dps[TEMPF_DPS] = 70

        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.target_temperature, 70)

    def test_minimum_target_temperature_f(self):
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.min_temp, 41)

    def test_maximum_target_temperature_f(self):
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.max_temp, 99)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "holiday"}
        ):
            await self.subject.async_set_temperature(preset_mode="holiday")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 25,
                PRESET_DPS: "program",
            },
        ):
            await self.subject.async_set_temperature(
                temperature=25, preset_mode="program"
            )

    async def test_set_target_temperature_fails_outside_valid_range_f(self):
        self.dps[UNIT_DPS] = "f"
        with self.assertRaisesRegex(
            ValueError, "temp_f \\(40\\) must be between 41 and 99"
        ):
            await self.subject.async_set_target_temperature(40)

        with self.assertRaisesRegex(
            ValueError, "temp_f \\(100\\) must be between 41 and 99"
        ):
            await self.subject.async_set_target_temperature(100)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 251
        self.dps[CURTEMPF_DPS] = 783
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.current_temperature, 25.1)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.current_temperature, 78.3)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[PRESET_DPS] = "manual"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[PRESET_DPS] = "program"
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)
        self.dps[PRESET_DPS] = "holiday"
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        )

    async def test_set_hvac_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, PRESET_DPS: "manual"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_auto(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True, PRESET_DPS: "program"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.AUTO)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "manual"
        self.assertEqual(self.subject.preset_mode, "manual")

        self.dps[PRESET_DPS] = "program"
        self.assertEqual(self.subject.preset_mode, "program")

        self.dps[PRESET_DPS] = "holiday"
        self.assertEqual(self.subject.preset_mode, "holiday")

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["manual", "program", "holiday"],
        )

    async def test_set_preset_mode_to_program(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "program"},
        ):
            await self.subject.async_set_preset_mode("program")

    async def test_set_preset_mode_to_manual(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "manual"},
        ):
            await self.subject.async_set_preset_mode("manual")

    async def test_set_preset_mode_to_holiday(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "holiday"},
        ):
            await self.subject.async_set_preset_mode("holiday")

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[HVACACTION_DPS] = "start"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

        self.dps[HVACACTION_DPS] = "stop"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_action, HVACAction.OFF)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN12_DPS] = False
        self.dps[UNKNOWN32_DPS] = 32
        self.dps[UNKNOWN45_DPS] = 45
        self.dps[UNKNOWN105_DPS] = "unknown 105"

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_12": False,
                "unknown_32": 32,
                "unknown_45": 45,
                "unknown_105": "unknown 105",
            },
        )
