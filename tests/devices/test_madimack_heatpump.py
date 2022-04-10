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
from ..mixins.climate import TargetTemperatureTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
CURRENTTEMP_DPS = "102"
UNITS_DPS = "103"
POWERLEVEL_DPS = "104"
OPMODE_DPS = "105"
TEMPERATURE_DPS = "106"
UNKNOWN107_DPS = "107"
UNKNOWN108_DPS = "108"
UNKNOWN115_DPS = "115"
UNKNOWN116_DPS = "116"
UNKNOWN118_DPS = "118"
UNKNOWN120_DPS = "120"
UNKNOWN122_DPS = "122"
UNKNOWN124_DPS = "124"
UNKNOWN125_DPS = "125"
UNKNOWN126_DPS = "126"
UNKNOWN127_DPS = "127"
UNKNOWN128_DPS = "128"
UNKNOWN129_DPS = "129"
UNKNOWN130_DPS = "130"
UNKNOWN134_DPS = "134"
UNKNOWN135_DPS = "135"
UNKNOWN136_DPS = "136"
UNKNOWN139_DPS = "139"
UNKNOWN140_DPS = "140"
PRESET_DPS = "117"


class TestMadimackPoolHeatpump(
    BasicSensorTests,
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
        self.setUpBasicSensor(
            POWERLEVEL_DPS,
            self.entities.get("sensor_power_level"),
            device_class=SensorDeviceClass.POWER_FACTOR,
            unit=PERCENTAGE,
        )
        self.mark_secondary(["sensor_power_level"])

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
        self.assertEqual(self.subject.min_temp, 60)

    def test_maximum_fahrenheit_temperature(self):
        self.dps[UNITS_DPS] = False
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
        self.dps[POWERLEVEL_DPS] = 50
        self.dps[UNKNOWN107_DPS] = 1
        self.dps[UNKNOWN108_DPS] = 2
        self.dps[UNKNOWN115_DPS] = 3
        self.dps[UNKNOWN116_DPS] = 4
        self.dps[UNKNOWN118_DPS] = 5
        self.dps[UNKNOWN120_DPS] = 6
        self.dps[UNKNOWN122_DPS] = 7
        self.dps[UNKNOWN124_DPS] = 8
        self.dps[UNKNOWN125_DPS] = 9
        self.dps[UNKNOWN126_DPS] = 10
        self.dps[UNKNOWN127_DPS] = 11
        self.dps[UNKNOWN128_DPS] = 12
        self.dps[UNKNOWN129_DPS] = 13
        self.dps[UNKNOWN130_DPS] = True
        self.dps[UNKNOWN134_DPS] = False
        self.dps[UNKNOWN135_DPS] = True
        self.dps[UNKNOWN136_DPS] = False
        self.dps[UNKNOWN139_DPS] = True
        self.dps[UNKNOWN140_DPS] = "test"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "power_level": 50,
                "unknown_107": 1,
                "unknown_108": 2,
                "unknown_115": 3,
                "unknown_116": 4,
                "unknown_118": 5,
                "unknown_120": 6,
                "unknown_122": 7,
                "unknown_124": 8,
                "unknown_125": 9,
                "unknown_126": 10,
                "unknown_127": 11,
                "unknown_128": 12,
                "unknown_129": 13,
                "unknown_130": True,
                "unknown_134": False,
                "unknown_135": True,
                "unknown_136": False,
                "unknown_139": True,
                "unknown_140": "test",
            },
        )
