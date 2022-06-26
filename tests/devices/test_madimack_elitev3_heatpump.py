from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from ..const import MADIMACK_ELITEV3_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
HVACMODE_DPS = "2"
TEMPERATURE_DPS = "4"
PRESET_DPS = "5"
UNIT_DPS = "6"
UNKNOWN15_DPS = "15"
PWRLEVEL_DPS = "20"
TEMPMAX_DPS = "21"
TEMPMIN_DPS = "22"
COILTEMP_DPS = "23"
EXHAUSTTEMP_DPS = "24"
OUTLETTEMP_DPS = "25"
AMBIENTTEMP_DPS = "26"
UNKNOWN101_DPS = "101"
CURRENTTEMP_DPS = "102"
RETURNGASTEMP_DPS = "103"
COOLCOILTEMP_DPS = "104"
COOLPLATETEMP_DPS = "105"
EEVOPENING_DPS = "106"
UNKNOWN107_DPS = "107"


class TestMadimackEliteV3Heatpump(
    MultiSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "madimack_elite_v3_heatpump.yaml",
            MADIMACK_ELITEV3_HEATPUMP_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=18,
            max=40,
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_power_level",
                    "dps": PWRLEVEL_DPS,
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "unit": PERCENTAGE,
                },
                {
                    "name": "sensor_evaporator_coil_pipe_temperature",
                    "dps": COILTEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_exhaust_gas_temperature",
                    "dps": EXHAUSTTEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_outlet_water_temperature",
                    "dps": OUTLETTEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_ambient_temperature",
                    "dps": AMBIENTTEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_return_gas_temperature",
                    "dps": RETURNGASTEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_cooling_coil_pipe_temperature",
                    "dps": COOLCOILTEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_cooling_plate_temperature",
                    "dps": COOLPLATETEMP_DPS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": TEMP_CELSIUS,
                },
                {
                    "name": "sensor_eev_opening",
                    "dps": EEVOPENING_DPS,
                },
            ]
        )
        self.mark_secondary(
            [
                "sensor_power_level",
                "sensor_evaporator_coil_pipe_temperature",
                "sensor_exhaust_gas_temperature",
                "sensor_outlet_water_temperature",
                "sensor_ambient_temperature",
                "sensor_return_gas_temperature",
                "sensor_cooling_coil_pipe_temperature",
                "sensor_cooling_plate_temperature",
                "sensor_eev_opening",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
            ),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:refresh-auto")
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "heating"
        self.assertEqual(self.subject.icon, "mdi:hot-tub")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_minimum_target_temperature(self):
        self.dps[TEMPMIN_DPS] = 60
        self.assertEqual(self.subject.min_temp, 60)

    def test_maximum_target_temperature(self):
        self.dps[TEMPMAX_DPS] = 104
        self.assertEqual(self.subject.max_temp, 104)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[HVACMODE_DPS] = "heating"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.HEAT_COOL],
        )

    async def test_set_hvac_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "cold"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "heating"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "auto"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def test_set_hvac_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "silence"
        self.assertEqual(self.subject.preset_mode, "Silence")
        self.dps[PRESET_DPS] = "power"
        self.assertEqual(self.subject.preset_mode, "Perfect")
        self.dps[PRESET_DPS] = "boost"
        self.assertEqual(self.subject.preset_mode, "Power")

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Silence", "Perfect", "Power"],
        )

    async def test_set_preset_to_silence(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "silence"},
        ):
            await self.subject.async_set_preset_mode("Silence")

    async def test_set_preset_to_perfect(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "power"},
        ):
            await self.subject.async_set_preset_mode("Perfect")

    async def test_set_preset_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "boost"},
        ):
            await self.subject.async_set_preset_mode("Power")

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN15_DPS] = 15
        self.dps[UNKNOWN101_DPS] = 101
        self.dps[UNKNOWN107_DPS] = True

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_15": 15,
                "unknown_101": 101,
                "unknown_107": True,
            },
        )
