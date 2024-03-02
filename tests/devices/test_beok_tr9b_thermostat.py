from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.const import PRECISION_TENTHS, UnitOfTemperature

from ..const import BEOK_TR9B_PAYLOAD
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
HVACMODE_DPS = "2"
ANTIFROST_DPS = "10"
TEMPERATURE_DPS = "16"
MAXTEMP_DPS = "19"
UNIT_DPS = "23"
CURRENTTEMP_DPS = "24"
MINTEMP_DPS = "26"
SCHED_DPS = "31"
VALVE_DPS = "36"
LOCK_DPS = "40"
ERROR_DPS = "45"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"


class TestBeokTR9BThermostat(
    MultiBinarySensorTests,
    BasicLockTests,
    MultiNumberTests,
    MultiSelectTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "beok_tr9b_thermostat.yaml",
            BEOK_TR9B_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=41.0,
            max=99.0,
            scale=10,
            step=10,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpMultiSelect(
            [
                {
                    "dps": SCHED_DPS,
                    "name": "select_schedule",
                    "options": {
                        "5_2": "Weekday+Weekend",
                        "6_1": "Mon-Sat+Sun",
                        "7": "Daily",
                    },
                },
                {
                    "dps": UNIT_DPS,
                    "name": "select_temperature_unit",
                    "options": {
                        "c": "celsius",
                        "f": "fahrenheit",
                    },
                },
            ],
        )
        self.setUpBasicSwitch(
            ANTIFROST_DPS,
            self.entities.get("switch_anti_frost"),
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "dps": ERROR_DPS,
                    "name": "binary_sensor_problem",
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (1, 0),
                },
                {
                    "dps": VALVE_DPS,
                    "name": "binary_sensor_valve",
                    "device_class": BinarySensorDeviceClass.OPENING,
                    "testdata": ("open", "close"),
                },
            ],
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": MINTEMP_DPS,
                    "name": "number_low_temperature_limit",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 5.0,
                    "max": 1000.0,
                    "step": 1.0,
                    "scale": 10,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": MAXTEMP_DPS,
                    "name": "number_high_temperature_limit",
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 5.0,
                    "max": 1000.0,
                    "step": 1.0,
                    "scale": 10,
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ],
        )
        self.mark_secondary(
            [
                "binary_sensor_problem",
                "binary_sensor_valve",
                "lock_child_lock",
                "number_low_temperature_limit",
                "number_high_temperature_limit",
                "select_schedule",
                "select_temperature_unit",
                "switch_anti_frost",
            ],
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON,
        )

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.CELSIUS,
        )
        self.assertEqual(self.subject.target_temperature_step, 0.5)

        self.dps[UNIT_DPS] = "f"
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.FAHRENHEIT,
        )
        self.assertEqual(self.subject.target_temperature_step, 1.0)

    def test_precision(self):
        self.assertEqual(self.subject.precision, PRECISION_TENTHS)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 685
        self.assertEqual(self.subject.current_temperature, 68.5)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = False
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

        self.dps[POWER_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)

        self.dps[HVACMODE_DPS] = "manual"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.HEAT,
                HVACMode.AUTO,
                HVACMode.OFF,
            ],
        )

    # Override - since min and max are set by attributes, the range
    # allowed when setting is wider than normal.  The thermostat seems
    # to be configurable as at least a water heater (to 212F), as tuya
    # doc says max 1000.0 (after scaling)
    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError,
            "temperature \\(4.5\\) must be between 5.0 and 1000.0",
        ):
            await self.subject.async_set_target_temperature(4.5)
        with self.assertRaisesRegex(
            ValueError,
            "temperature \\(1001\\) must be between 5.0 and 1000.0",
        ):
            await self.subject.async_set_target_temperature(1001)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN101_DPS] = 101
        self.dps[UNKNOWN102_DPS] = 102
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"unknown_101": 101, "unknown_102": 102},
        )

    def test_multi_bsensor_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 8
        self.assertDictEqual(
            self.multiBSensor["binary_sensor_problem"].extra_state_attributes,
            {"fault_code": 8},
        )
