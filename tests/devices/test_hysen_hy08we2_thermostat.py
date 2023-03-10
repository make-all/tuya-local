from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTime, UnitOfTemperature

from ..const import HYSEN_HY08WE2_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
LOCK_DPS = "6"
ERROR_DPS = "12"
UNIT_DPS = "101"
HVACACTION_DPS = "102"
EXTTEMP_DPS = "103"
HOLIDAYS_DPS = "104"
HOLIDAYTEMP_DPS = "105"
UNKNOWN106_DPS = "106"
UNKNOWN107_DPS = "107"
DISPLAY_DPS = "108"
CALIBOFFSET_DPS = "109"
CALIBSWINGINT_DPS = "110"
CALIBSWINGEXT_DPS = "111"
HIGHTEMP_DPS = "112"
LOWTEMP_DPS = "113"
MAXTEMP_DPS = "114"
MINTEMP_DPS = "115"
SENSOR_DPS = "116"
INITIAL_DPS = "117"
SCHED_DPS = "118"


class TestHysenHY08WE2Thermostat(
    BasicBinarySensorTests,
    BasicLockTests,
    BasicSensorTests,
    MultiNumberTests,
    MultiSelectTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "hysen_hy08we2_thermostat.yaml",
            HYSEN_HY08WE2_THERMOSTAT_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5.0,
            max=30.0,
            scale=10,
            step=5,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_fault"),
            testdata=(1, 0),
            device_class=BinarySensorDeviceClass.PROBLEM,
        )

        self.setUpMultiSelect(
            [
                {
                    "dps": SCHED_DPS,
                    "name": "select_schedule",
                    "options": {
                        "2days": "5 + 2 day",
                        "1days": "6 + 1 day",
                        "0days": "7 day",
                    },
                },
                {
                    "dps": INITIAL_DPS,
                    "name": "select_initial_state",
                    "options": {
                        "keep": "Previous",
                        "on": "On",
                        "off": "Off",
                    },
                },
                {
                    "dps": SENSOR_DPS,
                    "name": "select_temperature_sensor",
                    "options": {
                        "in": "Internal",
                        "ext": "External",
                        "all": "Both",
                    },
                },
                {
                    "dps": UNIT_DPS,
                    "name": "select_temperature_unit",
                    "options": {
                        False: "Celsius",
                        True: "Fahrenheit",
                    },
                },
            ],
        )
        self.setUpBasicSensor(
            EXTTEMP_DPS,
            self.entities.get("sensor_external_temperature"),
            device_class=SensorDeviceClass.TEMPERATURE,
            testdata=(205, 20.5),
            unit=UnitOfTemperature.CELSIUS,
            state_class="measurement",
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": HOLIDAYS_DPS,
                    "name": "number_holiday_days",
                    "min": 1,
                    "max": 30,
                    "unit": UnitOfTime.DAYS,
                },
                {
                    "dps": HOLIDAYTEMP_DPS,
                    "name": "number_holiday_temperature",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 5,
                    "max": 30,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": CALIBOFFSET_DPS,
                    "name": "number_calibration_offset",
                    "min": -9,
                    "max": 9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": CALIBSWINGINT_DPS,
                    "name": "number_calibration_swing_internal",
                    "min": 0.5,
                    "max": 2.5,
                    "scale": 10,
                    "step": 0.1,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": CALIBSWINGEXT_DPS,
                    "name": "number_calibration_swing_external",
                    "min": 0.1,
                    "max": 1.0,
                    "scale": 10,
                    "step": 0.1,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": HIGHTEMP_DPS,
                    "name": "number_high_temperature_protection",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 35,
                    "max": 70,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": LOWTEMP_DPS,
                    "name": "number_low_temperature_protection",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 1,
                    "max": 10,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": MINTEMP_DPS,
                    "name": "number_low_temperature_limit",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 1,
                    "max": 10,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": MAXTEMP_DPS,
                    "name": "number_high_temperature_limit",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 2,
                    "max": 70,
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ],
        )
        self.mark_secondary(
            [
                "binary_sensor_fault",
                "lock_child_lock",
                "number_holiday_days",
                "number_holiday_temperature",
                "number_calibration_offset",
                "number_calibration_swing_internal",
                "number_calibration_swing_external",
                "number_high_temperature_protection",
                "number_low_temperature_protection",
                "number_low_temperature_limit",
                "number_high_temperature_limit",
                "select_initial_state",
                "select_schedule",
                "select_temperature_sensor",
                "select_temperature_unit",
            ],
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
            ),
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 685
        self.assertEqual(self.subject.current_temperature, 68.5)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.HEAT,
                HVACMode.OFF,
            ],
        )

    async def test_set_hvac_mode_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: True},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[HVACACTION_DPS] = True
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)
        self.dps[HVACACTION_DPS] = False
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_action, HVACAction.OFF)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Manual", "Program", "Program Override", "Holiday"],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "Manual"
        self.assertEqual(self.subject.preset_mode, "Manual")
        self.dps[PRESET_DPS] = "Program"
        self.assertEqual(self.subject.preset_mode, "Program")
        self.dps[PRESET_DPS] = "TempProg"
        self.assertEqual(self.subject.preset_mode, "Program Override")
        self.dps[PRESET_DPS] = "Holiday"
        self.assertEqual(self.subject.preset_mode, "Holiday")

    # Override - since min and max are set by attributes, the range
    # allowed when setting is wider than normal.  The thermostat seems
    # to be configurable as at least a water heater (to 212F), as tuya
    # doc says max 1000.0 (after scaling)
    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError,
            f"temperature \\(0\\) must be between 0.5 and 122.0",
        ):
            await self.subject.async_set_target_temperature(0)
        with self.assertRaisesRegex(
            ValueError,
            f"temperature \\(122.5\\) must be between 0.5 and 122.0",
        ):
            await self.subject.async_set_target_temperature(122.5)

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 12
        self.dps[UNKNOWN106_DPS] = False
        self.dps[UNKNOWN107_DPS] = True
        self.dps[DISPLAY_DPS] = True
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "fault_code": 12,
                "unknown_106": False,
                "unknown_107": True,
                "temperature_display": "external",
            },
        )
        self.dps[DISPLAY_DPS] = False
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "fault_code": 12,
                "unknown_106": False,
                "unknown_107": True,
                "temperature_display": "internal",
            },
        )

    def test_icons(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")
