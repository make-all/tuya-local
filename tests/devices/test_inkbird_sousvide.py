from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import INKBIRD_SOUSVIDE_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "101"
HVACACTION_DPS = "102"
TEMPERATURE_DPS = "103"
CURRENTTEMP_DPS = "104"
TIMER_DPS = "105"
REMAIN_DPS = "106"
ERROR_DPS = "107"
UNIT_DPS = "108"
RECIPE_DPS = "109"
CALIBRATE_DPS = "110"


class TestInkbirdSousVideCooker(
    BasicBinarySensorTests,
    MultiNumberTests,
    BasicSelectTests,
    BasicSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("inkbird_sousvide_cooker.yaml", INKBIRD_SOUSVIDE_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=0.0,
            max=96.0,
            scale=10,
        )
        self.setUpMultiNumber(
            [
                {
                    "dps": TIMER_DPS,
                    "name": "number_cooking_time",
                    "max": 5999,
                    "unit": UnitOfTime.MINUTES,
                },
                {
                    "dps": RECIPE_DPS,
                    "name": "number_recipe",
                    "max": 1000,
                },
                {
                    "dps": CALIBRATE_DPS,
                    "name": "number_temperature_calibration",
                    "min": -9.9,
                    "max": 9.9,
                    "scale": 10,
                    "step": 0.1,
                },
            ]
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpBasicSelect(
            UNIT_DPS,
            self.entities.get("select_temperature_unit"),
            {
                False: "fahrenheit",
                True: "celsius",
            },
        )
        self.setUpBasicSensor(
            REMAIN_DPS,
            self.entities.get("sensor_time_remaining"),
            unit=UnitOfTime.MINUTES,
            device_class=SensorDeviceClass.DURATION,
        )
        self.mark_secondary(
            [
                "number_cooking_time",
                "number_recipe",
                "number_temperature_calibration",
                "binary_sensor_problem",
                "select_temperature_unit",
                "sensor_time_remaining",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON,
        )

    def test_icon(self):
        self.dps[ERROR_DPS] = 0
        self.dps[HVACACTION_DPS] = "stop"
        self.assertEqual(self.subject.icon, "mdi:pot-outline")

        self.dps[HVACACTION_DPS] = "working"
        self.assertEqual(self.subject.icon, "mdi:pot-steam")
        self.dps[HVACACTION_DPS] = "complete"
        self.assertEqual(self.subject.icon, "mdi:pot")

        self.dps[ERROR_DPS] = 2
        self.assertEqual(self.subject.icon, "mdi:alert")

    def test_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 522
        self.assertEqual(self.subject.current_temperature, 52.2)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[HVACACTION_DPS] = "stop"
        self.assertEqual(self.subject.hvac_action, HVACAction.OFF)

        self.dps[HVACACTION_DPS] = "working"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

        self.dps[HVACACTION_DPS] = "complete"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_action, HVACAction.OFF)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_extra_state_attributes(self):
        # There are currently no known error states; update this as
        # they are discovered
        self.dps[ERROR_DPS] = 2
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"fault": 2},
        )
        self.dps[ERROR_DPS] = "0"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"fault": 0},
        )
