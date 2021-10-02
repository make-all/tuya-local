from homeassistant.components.climate.const import (
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT


from ..const import INKBIRD_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
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
ALARM_TIME_DPS = "113"
TEMPHIGH_DPS = "114"
SWITCH_DPS = "115"
TEMPF_DPS = "116"
UNKNOWN117_DPS = "117"
UNKNOWN118_DPS = "118"
UNKNOWN119_DPS = "119"
UNKNOWN120_DPS = "120"


class TestInkbirdThermostat(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "inkbird_itc306a_thermostat.yaml", INKBIRD_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")

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
        self.assertEqual(self.subject.icon, "mdi:thermometer-alert")

        self.dps[ALARM_LOW_DPS] = False
        self.dps[ALARM_TIME_DPS] = True
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
            {"On", "Pause", "Off"},
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
        self.dps[CURRENTTEMP_DPS] = 289
        self.assertEqual(self.subject.current_temperature, 28.9)

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

    def test_minimum_target_temperature(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.min_temp, 20.0)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.min_temp, 68.0)

    def test_maximum_target_temperature(self):
        self.dps[UNIT_DPS] = "C"
        self.assertEqual(self.subject.max_temp, 35.0)
        self.dps[UNIT_DPS] = "F"
        self.assertEqual(self.subject.max_temp, 95.0)

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
            ValueError, "target_temp_low \\(19.9\\) must be between 20.0 and 35.0"
        ):
            await self.subject.async_set_temperature(
                target_temp_high=32.2, target_temp_low=19.9
            )

        self.dps[UNIT_DPS] = "F"
        with self.assertRaisesRegex(
            ValueError, "target_temp_high \\(95.1\\) must be between 68.0 and 95.0"
        ):
            await self.subject.async_set_temperature(
                target_temp_low=70.0, target_temp_high=95.1
            )

    def test_device_state_attributes(self):
        self.dps[ERROR_DPS] = 1
        self.dps[CALIBRATE_DPS] = 1
        self.dps[TIME_THRES_DPS] = 5
        self.dps[HIGH_THRES_DPS] = 400
        self.dps[LOW_THRES_DPS] = 300
        self.dps[ALARM_HIGH_DPS] = True
        self.dps[ALARM_LOW_DPS] = False
        self.dps[ALARM_TIME_DPS] = True
        self.dps[SWITCH_DPS] = False
        self.dps[TEMPF_DPS] = 999
        self.dps[UNKNOWN117_DPS] = True
        self.dps[UNKNOWN118_DPS] = False
        self.dps[UNKNOWN119_DPS] = True
        self.dps[UNKNOWN120_DPS] = False

        self.assertCountEqual(
            self.subject.device_state_attributes,
            {
                "error": 1,
                "temperature_calibration_offset": 0.1,
                "heat_time_alarm_threshold_hours": 5,
                "high_temp_alarm_threshold": 40.0,
                "low_temp_alarm_threshold": 30.0,
                "high_temp_alarm": True,
                "low_temp_alarm": False,
                "heat_time_alarm": True,
                "switch_state": False,
                "current_temperature_f": 99.9,
                "unknown_117": True,
                "unknown_118": False,
                "unknown_119": True,
                "unknown_120": False,
            },
        )
