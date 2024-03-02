from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import ClimateEntityFeature, HVACAction
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import INKBIRD_ITC308_THERMOSTAT_PAYLOAD
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

ERROR_DPS = "12"
UNIT_DPS = "101"
CALIBRATE_DPS = "102"
CURRENTTEMP_DPS = "104"
TEMPERATURE_DPS = "106"
TIME_THRES_DPS = "108"
HIGH_THRES_DPS = "109"
LOW_THRES_DPS = "110"
ALARM_HIGH_DPS = "111"
ALARM_LOW_DPS = "112"
ALARM_SENSOR_DPS = "113"
STATUS_DPS = "115"
TEMPF_DPS = "116"
HEATDIFF_DPS = "117"
COOLDIFF_DPS = "118"


class TestInkbirdITC308Thermostat(
    BasicSelectTests,
    MultiBinarySensorTests,
    MultiNumberTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "inkbird_itc308_thermostat.yaml", INKBIRD_ITC308_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=-50.0,
            max=99.9,
            scale=10,
        )
        self.setUpBasicSelect(
            UNIT_DPS,
            self.entities.get("select_temperature_unit"),
            {
                "C": "celsius",
                "F": "fahrenheit",
            },
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "name": "binary_sensor_high_temperature",
                    "dps": ALARM_HIGH_DPS,
                    "device_class": BinarySensorDeviceClass.HEAT,
                },
                {
                    "name": "binary_sensor_low_temperature",
                    "dps": ALARM_LOW_DPS,
                    "device_class": BinarySensorDeviceClass.COLD,
                },
                {
                    "name": "binary_sensor_sensor_fault",
                    "dps": ALARM_SENSOR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                },
                {
                    "name": "binary_sensor_problem",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (1, 0),
                },
            ]
        )
        self.setUpMultiNumber(
            [
                {
                    "name": "number_calibration_offset",
                    "dps": CALIBRATE_DPS,
                    "scale": 10,
                    "step": 0.1,
                    "min": -9.9,
                    "max": 9.9,
                },
                {
                    "name": "number_compressor_delay",
                    "dps": TIME_THRES_DPS,
                    "max": 10,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "name": "number_high_temperature_limit",
                    "dps": HIGH_THRES_DPS,
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "scale": 10,
                    "step": 0.1,
                    "min": -50,
                    "max": 99.9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_low_temperature_limit",
                    "dps": LOW_THRES_DPS,
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "scale": 10,
                    "step": 0.1,
                    "min": -50,
                    "max": 99.9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_cooling_hysteresis",
                    "dps": COOLDIFF_DPS,
                    "scale": 10,
                    "step": 0.1,
                    "min": 0.3,
                    "max": 15.0,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_heating_hysteresis",
                    "dps": HEATDIFF_DPS,
                    "scale": 10,
                    "step": 0.1,
                    "min": 0.3,
                    "max": 15.0,
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ]
        )
        self.mark_secondary(
            [
                "select_temperature_unit",
                "binary_sensor_high_temperature",
                "binary_sensor_low_temperature",
                "binary_sensor_sensor_fault",
                "binary_sensor_problem",
                "number_calibration_offset",
                "number_compressor_delay",
                "number_high_temperature_limit",
                "number_low_temperature_limit",
                "number_cooling_hysteresis",
                "number_heating_hysteresis",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE,
        )

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[ALARM_HIGH_DPS] = False
        self.dps[ALARM_LOW_DPS] = False
        self.dps[ALARM_SENSOR_DPS] = False
        self.dps[STATUS_DPS] = "3"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[STATUS_DPS] = "1"
        self.assertEqual(self.subject.icon, "mdi:snowflake")

        self.dps[STATUS_DPS] = "2"
        self.assertEqual(self.subject.icon, "mdi:thermometer-off")

        self.dps[ALARM_HIGH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

        self.dps[STATUS_DPS] = "3"
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

        self.dps[ALARM_HIGH_DPS] = False
        self.dps[ALARM_LOW_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:snowflake-alert")

        self.dps[ALARM_LOW_DPS] = False
        self.dps[ALARM_SENSOR_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

    def test_climate_hvac_modes(self):
        self.assertEqual(self.subject.hvac_modes, ["auto"])

    def test_current_temperature(self):
        self.dps[UNIT_DPS] = "C"
        self.dps[CURRENTTEMP_DPS] = 289
        self.assertEqual(self.subject.current_temperature, 28.9)
        self.dps[UNIT_DPS] = "F"
        self.dps[TEMPF_DPS] = 789
        self.assertEqual(self.subject.current_temperature, 78.9)

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_hvac_action(self):
        self.dps[STATUS_DPS] = "1"
        self.assertEqual(self.subject.hvac_action, HVACAction.COOLING)
        self.dps[STATUS_DPS] = "2"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)
        self.dps[STATUS_DPS] = "3"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 12

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": 12,
            },
        )
