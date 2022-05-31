from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from ..const import MADIMACK_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
CURRENTTEMP_DPS = "102"
UNITS_DPS = "103"
POWERLEVEL_DPS = "104"
OPMODE_DPS = "105"
TEMPERATURE_DPS = "106"
MINTEMP_DPS = "107"
MAXTEMP_DPS = "108"
ERROR_DPS = "115"
UNKNOWN116_DPS = "116"
UNKNOWN118_DPS = "118"
COIL_DPS = "120"
EXHAUST_DPS = "122"
AMBIENT_DPS = "124"
COMPRESSOR_DPS = "125"
UNKNOWN126_DPS = "126"
COOLINGPLATE_DPS = "127"
EEV_DPS = "128"
FANSPEED_DPS = "129"
UNKNOWN130_DPS = "130"
UNKNOWN134_DPS = "134"
UNKNOWN135_DPS = "135"
UNKNOWN136_DPS = "136"
UNKNOWN139_DPS = "139"
UNKNOWN140_DPS = "140"
PRESET_DPS = "117"


class TestMadimackPoolHeatpump(
    BasicBinarySensorTests,
    MultiSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("madimack_heatpump.yaml", MADIMACK_HEATPUMP_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=18,
            max=45,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_water_flow"),
            device_class=DEVICE_CLASS_PROBLEM,
            testdata=(4, 0),
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": POWERLEVEL_DPS,
                    "name": "sensor_power_level",
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "unit": PERCENTAGE,
                },
                {
                    "dps": COIL_DPS,
                    "name": "sensor_evaporator_coil_pipe_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": EXHAUST_DPS,
                    "name": "sensor_exhaust_gas_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": AMBIENT_DPS,
                    "name": "sensor_ambient_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": COMPRESSOR_DPS,
                    "name": "sensor_compressor_speed",
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "unit": PERCENTAGE,
                },
                {
                    "dps": COOLINGPLATE_DPS,
                    "name": "sensor_cooling_plate_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "dps": EEV_DPS,
                    "name": "sensor_eev_opening",
                },
                {
                    "dps": FANSPEED_DPS,
                    "name": "sensor_fan_speed",
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_power_level",
                "sensor_ambient_temperature",
                "sensor_compressor_speed",
                "sensor_cooling_plate_temperature",
                "sensor_evaporator_coil_pipe_temperature",
                "sensor_eev_opening",
                "sensor_exhaust_gas_temperature",
                "sensor_fan_speed",
                "binary_sensor_water_flow",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:hot-tub")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNITS_DPS] = False
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)
        self.dps[UNITS_DPS] = True
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

    def test_minimum_fahrenheit_temperature(self):
        self.dps[UNITS_DPS] = False
        self.dps[MINTEMP_DPS] = 60
        self.assertEqual(self.subject.min_temp, 60)

    def test_maximum_fahrenheit_temperature(self):
        self.dps[UNITS_DPS] = False
        self.dps[MAXTEMP_DPS] = 115
        self.assertEqual(self.subject.max_temp, 115)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = False
        self.assertEqual(self.subject.preset_mode, "Silent")

        self.dps[PRESET_DPS] = True
        self.assertEqual(self.subject.preset_mode, "Boost")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["Silent", "Boost"])

    async def test_set_preset_mode_to_silent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: False},
        ):
            await self.subject.async_set_preset_mode("Silent")

    async def test_set_preset_mode_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: True},
        ):
            await self.subject.async_set_preset_mode("Boost")

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[OPMODE_DPS] = "heating"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_HEAT)
        self.dps[OPMODE_DPS] = "warm"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_IDLE)
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_OFF)

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 4
        self.dps[UNKNOWN116_DPS] = 4
        self.dps[UNKNOWN118_DPS] = 5
        self.dps[UNKNOWN126_DPS] = 10
        self.dps[UNKNOWN130_DPS] = True
        self.dps[UNKNOWN134_DPS] = False
        self.dps[UNKNOWN135_DPS] = True
        self.dps[UNKNOWN136_DPS] = False
        self.dps[UNKNOWN139_DPS] = True
        self.dps[UNKNOWN140_DPS] = "test"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": "Water Flow Protection",
                "unknown_116": 4,
                "unknown_118": 5,
                "unknown_126": 10,
                "unknown_130": True,
                "unknown_134": False,
                "unknown_135": True,
                "unknown_136": False,
                "unknown_139": True,
                "unknown_140": "test",
            },
        )
