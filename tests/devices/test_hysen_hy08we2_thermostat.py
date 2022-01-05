from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
    TIME_DAYS,
)

from ..const import HYSEN_HY08WE2_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
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
UNKNOWN12_DPS = "12"
UNKNOWN101_DPS = "101"
HVACACTION_DPS = "102"
EXTTEMP_DPS = "103"
HOLIDAYS_DPS = "104"
HOLIDAYTEMP_DPS = "105"
UNKNOWN106_DPS = "106"
UNKNOWN107_DPS = "107"
UNKNOWN108_DPS = "108"
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
    BasicLockTests,
    MultiNumberTests,
    MultiSelectTests,
    BasicSensorTests,
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
            ],
        )
        self.setUpBasicSensor(
            EXTTEMP_DPS,
            self.entities.get("sensor_external_temperature"),
            device_class=DEVICE_CLASS_TEMPERATURE,
            testdata=(205, 20.5),
            unit=TEMP_CELSIUS,
            state_class="measurement",
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": HOLIDAYS_DPS,
                    "name": "number_holiday_days",
                    "min": 1,
                    "max": 30,
                    "unit": TIME_DAYS,
                },
                {
                    "dps": HOLIDAYTEMP_DPS,
                    "name": "number_holiday_temperature",
                    "min": 5,
                    "max": 30,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": CALIBOFFSET_DPS,
                    "name": "number_calibration_offset",
                    "min": -9,
                    "max": 9,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": CALIBSWINGINT_DPS,
                    "name": "number_calibration_swing_internal",
                    "min": 0.5,
                    "max": 2.5,
                    "scale": 10,
                    "step": 0.1,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": CALIBSWINGEXT_DPS,
                    "name": "number_calibration_swing_external",
                    "min": 0.1,
                    "max": 1.0,
                    "scale": 10,
                    "step": 0.1,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": HIGHTEMP_DPS,
                    "name": "number_high_temperature_protection",
                    "min": 35,
                    "max": 70,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": LOWTEMP_DPS,
                    "name": "number_low_temperature_protection",
                    "min": 1,
                    "max": 10,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": MINTEMP_DPS,
                    "name": "number_low_temperature_limit",
                    "min": 1,
                    "max": 10,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": MAXTEMP_DPS,
                    "name": "number_high_temperature_limit",
                    "min": 2,
                    "max": 70,
                    "unit": TEMP_CELSIUS,
                },
            ],
        )
        self.mark_secondary(
            [
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
                "select_temperature_sensor",
                "select_initial_state",
                "select_schedule",
            ],
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 685
        self.assertEqual(self.subject.current_temperature, 68.5)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_HEAT,
                HVAC_MODE_OFF,
            ],
        )

    async def test_set_hvac_mode_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: True},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_set_hvac_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[HVACACTION_DPS] = True
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_HEAT)
        self.dps[HVACACTION_DPS] = False
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_IDLE)
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_OFF)

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
        self.dps[UNKNOWN12_DPS] = 12
        self.dps[UNKNOWN101_DPS] = True
        self.dps[UNKNOWN106_DPS] = False
        self.dps[UNKNOWN107_DPS] = True
        self.dps[UNKNOWN108_DPS] = False
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_12": 12,
                "unknown_101": True,
                "unknown_106": False,
                "unknown_107": True,
                "unknown_108": False,
            },
        )

    def test_icons(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")
