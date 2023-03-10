from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    PRESET_AWAY,
    PRESET_HOME,
)
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfPower, UnitOfTemperature

from ..const import SASWELL_C16_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

TEMPERATURE_DPS = "2"
PRESET_DPS = "3"
UNKNOWN4_DPS = "4"
CURRENTTEMP_DPS = "5"
FLOORTEMPLIMIT_DPS = "6"
INSTALL_DPS = "7"
FLOORTEMP_DPS = "8"
HVACMODE_DPS = "9"
ADAPTIVE_DPS = "10"
LOCK_DPS = "11"
SCHED_DPS = "12"
SENSOR_DPS = "14"
ROOMCALIB_DPS = "15"
FLOORCALIB_DPS = "17"
UNKNOWN21_DPS = "21"
POWERRATING_DPS = "22"
UNKNOWN23_DPS = "23"
HVACACTION_DPS = "24"
UNKNOWN26_DPS = "26"


class TestSaswellC16Thermostat(
    BasicLockTests,
    BasicSensorTests,
    BasicSwitchTests,
    MultiNumberTests,
    MultiSelectTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "saswell_c16_thermostat.yaml", SASWELL_C16_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5.0,
            max=40.0,
            scale=10,
            step=5,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSensor(
            FLOORTEMP_DPS,
            self.entities.get("sensor_floor_temperature"),
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class="measurement",
            unit=UnitOfTemperature.CELSIUS,
            testdata=(218, 21.8),
        )
        self.setUpBasicSwitch(ADAPTIVE_DPS, self.entities.get("switch_adaptive"))
        self.setUpMultiNumber(
            [
                {
                    "name": "number_floor_temperature_limit",
                    "dps": FLOORTEMPLIMIT_DPS,
                    "device_class": NumberDeviceClass.TEMPERATURE,
                    "min": 20.0,
                    "max": 50.0,
                    "scale": 10,
                    "step": 0.5,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_power_rating",
                    "dps": POWERRATING_DPS,
                    "device_class": NumberDeviceClass.POWER,
                    "max": 3500,
                    "unit": UnitOfPower.WATT,
                },
                {
                    "name": "number_room_temperature_calibration",
                    "dps": ROOMCALIB_DPS,
                    "min": -5.0,
                    "max": 5.0,
                    "scale": 10,
                    "step": 0.5,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_floor_temperature_calibration",
                    "dps": FLOORCALIB_DPS,
                    "min": -5.0,
                    "max": 5.0,
                    "scale": 10,
                    "step": 0.5,
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ]
        )
        self.setUpMultiSelect(
            [
                {
                    "name": "select_installation",
                    "dps": INSTALL_DPS,
                    "options": {
                        True: "Office",
                        False: "Home",
                    },
                },
                {
                    "name": "select_schedule",
                    "dps": SCHED_DPS,
                    "options": {
                        "5_1_1": "Weekdays+Sat+Sun",
                        "7": "Daily",
                    },
                },
                {
                    "name": "select_sensor_select",
                    "dps": SENSOR_DPS,
                    "options": {
                        "0": "Floor sensor",
                        "1": "Room sensor",
                        "2": "Room sensor with floor sensor limit",
                        "3": "External room sensor",
                        "4": "External room sensor with floor sensor limit",
                    },
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "sensor_floor_temperature",
                "switch_adaptive",
                "number_floor_temperature_calibration",
                "number_floor_temperature_limit",
                "number_power_rating",
                "number_room_temperature_calibration",
                "select_installation",
                "select_schedule",
                "select_sensor_select",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
            ),
        )

    def test_icon(self):
        self.dps[PRESET_DPS] = "Smart"
        self.assertEqual(self.subject.icon, "mdi:home-thermometer")
        self.dps[PRESET_DPS] = "Manual"
        self.assertEqual(self.subject.icon, "mdi:cursor-pointer")
        self.dps[PRESET_DPS] = "Anti_frozen"
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")

    def test_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.CELSIUS,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 250
        self.assertEqual(self.subject.current_temperature, 25.0)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.COOL, HVACMode.HEAT],
        )

    async def test_set_hvac_mode_cool(self):
        with self.assertRaises(TypeError):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_heat(self):
        with self.assertRaises(TypeError):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    def test_hvac_action(self):
        self.dps[HVACACTION_DPS] = "Cooling"
        self.assertEqual(self.subject.hvac_action, HVACAction.COOLING)

        self.dps[HVACACTION_DPS] = "Heating"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

        self.dps[HVACACTION_DPS] = "Standby"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "Smart"
        self.assertEqual(self.subject.preset_mode, PRESET_HOME)
        self.dps[PRESET_DPS] = "Manual"
        self.assertEqual(self.subject.preset_mode, "manual")
        self.dps[PRESET_DPS] = "Anti_frozen"
        self.assertEqual(self.subject.preset_mode, PRESET_AWAY)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [PRESET_HOME, PRESET_AWAY, "manual"],
        )

    async def test_set_preset_to_away(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Anti_frozen"},
        ):
            await self.subject.async_set_preset_mode(PRESET_AWAY)

    async def test_set_preset_to_home(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Smart"},
        ):
            await self.subject.async_set_preset_mode(PRESET_HOME)

    async def test_set_preset_to_manual(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Manual"},
        ):
            await self.subject.async_set_preset_mode("manual")

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN4_DPS] = 4
        self.dps[FLOORTEMPLIMIT_DPS] = 355
        self.dps[INSTALL_DPS] = True
        self.dps[FLOORTEMP_DPS] = 251
        self.dps[ADAPTIVE_DPS] = False
        self.dps[SCHED_DPS] = "5_1_1"
        self.dps[UNKNOWN21_DPS] = True
        self.dps[POWERRATING_DPS] = 2000
        self.dps[UNKNOWN23_DPS] = 23
        self.dps[UNKNOWN26_DPS] = 26

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_4": 4,
                "floor_temp_limit": 35.5,
                "installation": "Office",
                "floor_temperature": 25.1,
                "adaptive": False,
                "schedule": "5_1_1",
                "unknown_21": True,
                "power_rating": 2000,
                "unknown_23": 23,
                "unknown_26": 26,
            },
        )
