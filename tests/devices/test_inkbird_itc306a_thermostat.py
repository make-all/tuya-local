from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, TIME_HOURS


from ..const import INKBIRD_ITC306A_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

ERROR_DPS = "12"
UNIT_DPS = "101"
CALIBRATE_DPS = "102"
PRESET_DPS = "103"
CURRENTTEMP_DPS = "104"
TEMPLOW_DPS = "106"
TIME_THRES_DPS = "108"
HIGH_THRES_DPS = "109"
LOW_THRES_DPS = "110"
ALARM_HIGH_DPS = "111"
ALARM_LOW_DPS = "112"
ALARM_DIFF_DPS = "113"
TEMPHIGH_DPS = "114"
SWITCH_DPS = "115"
TEMPF_DPS = "116"
UNKNOWN117_DPS = "117"
UNKNOWN118_DPS = "118"
UNKNOWN119_DPS = "119"
ALARM_TIME_DPS = "120"


class TestInkbirdThermostat(
    BasicSelectTests,
    MultiBinarySensorTests,
    MultiNumberTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "inkbird_itc306a_thermostat.yaml", INKBIRD_ITC306A_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpBasicSelect(
            UNIT_DPS,
            self.entities.get("select_temperature_unit"),
            {
                "C": "Celsius",
                "F": "Fahrenheit",
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
                    "name": "binary_sensor_continuous_heat",
                    "dps": ALARM_TIME_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                },
                {
                    "name": "binary_sensor_unbalanced",
                    "dps": ALARM_DIFF_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                },
                {
                    "name": "binary_sensor_error",
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
                    "name": "number_continuous_heat_hours",
                    "dps": TIME_THRES_DPS,
                    "max": 96,
                    "unit": TIME_HOURS,
                },
                {
                    "name": "number_high_temperature_limit",
                    "dps": HIGH_THRES_DPS,
                    "scale": 10,
                    "step": 0.1,
                    "min": -40,
                    "max": 100,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "number_low_temperature_limit",
                    "dps": LOW_THRES_DPS,
                    "scale": 10,
                    "step": 0.1,
                    "min": -40,
                    "max": 100,
                    "unit": TEMP_CELSIUS,
                },
            ]
        )
        self.mark_secondary(
            [
                "select_temperature_unit",
                "binary_sensor_high_temperature",
                "binary_sensor_low_temperature",
                "binary_sensor_continuous_heat",
                "binary_sensor_unbalanced",
                "binary_sensor_error",
                "number_calibration_offset",
                "number_continuous_heat_hours",
                "number_high_temperature_limit",
                "number_low_temperature_limit",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE_RANGE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[ALARM_HIGH_DPS] = False
        self.dps[ALARM_LOW_DPS] = False
        self.dps[ALARM_TIME_DPS] = False
        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:thermometer-off")

        self.dps[ALARM_HIGH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

        self.dps[ALARM_HIGH_DPS] = False
        self.dps[ALARM_LOW_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:snowflake-alert")

        self.dps[ALARM_LOW_DPS] = False
        self.dps[ALARM_TIME_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:clock-alert")

        self.dps[ALARM_TIME_DPS] = False
        self.dps[ALARM_DIFF_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

    def test_climate_hvac_modes(self):
        self.assertEqual(self.subject.hvac_modes, [])

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "on"
        self.assertEqual(self.subject.preset_mode, "On")

        self.dps[PRESET_DPS] = "pause"
        self.assertEqual(self.subject.preset_mode, "Pause")

        self.dps[PRESET_DPS] = "off"
        self.assertEqual(self.subject.preset_mode, "Off")

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["On", "Pause", "Off"],
        )

    async def test_set_preset_to_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "on",
            },
        ):
            await self.subject.async_set_preset_mode("On")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_preset_to_pause(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "pause",
            },
        ):
            await self.subject.async_set_preset_mode("Pause")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_preset_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "off",
            },
        ):
            await self.subject.async_set_preset_mode("Off")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_current_temperature(self):
        self.dps[UNIT_DPS] = "C"
        self.dps[CURRENTTEMP_DPS] = 289
        self.assertEqual(self.subject.current_temperature, 28.9)
        self.dps[UNIT_DPS] = "F"
        self.dps[TEMPF_DPS] = 789
        self.assertEqual(self.subject.current_temperature, 78.9)

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

    def test_minimum_target_temperature(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.min_temp, 0.0)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.min_temp, 32.0)

    def test_maximum_target_temperature(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.max_temp, 45.0)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.max_temp, 113.0)

    def test_temperature_range(self):
        self.dps[TEMPHIGH_DPS] = 301
        self.dps[TEMPLOW_DPS] = 255
        self.assertEqual(self.subject.target_temperature_high, 30.1)
        self.assertEqual(self.subject.target_temperature_low, 25.5)

    async def test_set_temperature_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPHIGH_DPS: 322,
                TEMPLOW_DPS: 266,
            },
        ):
            await self.subject.async_set_temperature(
                target_temp_high=32.2, target_temp_low=26.6
            )

    async def test_set_target_temperature_fails_outside_valid_range(self):
        self.dps[UNIT_DPS] = "C"
        with self.assertRaisesRegex(
            ValueError, "target_temp_low \\(-0.1\\) must be between 0.0 and 45.0"
        ):
            await self.subject.async_set_temperature(
                target_temp_high=32.2, target_temp_low=-0.1
            )

        self.dps[UNIT_DPS] = "F"
        with self.assertRaisesRegex(
            ValueError, "target_temp_high \\(113.1\\) must be between 32.0 and 113.0"
        ):
            await self.subject.async_set_temperature(
                target_temp_low=70.0, target_temp_high=113.1
            )

    def test_hvac_action(self):
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_IDLE)
        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_HEAT)

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 1
        self.dps[UNKNOWN117_DPS] = True
        self.dps[UNKNOWN118_DPS] = False
        self.dps[UNKNOWN119_DPS] = True

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": 1,
                "unknown_117": True,
                "unknown_118": False,
                "unknown_119": True,
            },
        )
