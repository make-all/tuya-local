from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass
from homeassistant.const import UnitOfEnergy, UnitOfTemperature

from ..const import JIAHONG_ET72W_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "101"
TEMPERATURE_DPS = "102"
HVACMODE_DPS = "103"
UNKNOWN104_DPS = "104"
CURRENTTEMP_DPS = "105"
FLOORTEMP_DPS = "106"
UNIT_DPS = "107"
LOCK_DPS = "108"
UNKNOWN109_DPS = "109"
SCHED_DPS = "110"
SENSOR_DPS = "111"
UNKNOWN112_DPS = "112"
UNKNOWN113_DPS = "113"
CALIB_DPS = "116"
ENERGY_DPS = "117"
HVACACTION_DPS = "118"
TEMPLIMIT_DPS = "121"


class TestJiahongEt72wThermostat(
    BasicLockTests,
    BasicNumberTests,
    MultiSelectTests,
    MultiSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "jiahong_et72w_thermostat.yaml",
            JIAHONG_ET72W_PAYLOAD,
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
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_screen_lock"))
        self.setUpMultiSelect(
            [
                {
                    "dps": SCHED_DPS,
                    "name": "select_auto_schedule",
                    "options": {
                        0: "7",
                        1: "5+1+1",
                        2: "7 (Adaptive)",
                        3: "5+1+1 (Adaptive)",
                    },
                },
                {
                    "dps": UNIT_DPS,
                    "name": "select_temperature_unit",
                    "options": {
                        False: "Celsius",
                        True: "Fahrenheit",
                    },
                },
                {
                    "dps": SENSOR_DPS,
                    "name": "select_temperature_sensor",
                    "options": {
                        "0": "Room",
                        "1": "Floor",
                        "2": "Both",
                    },
                },
            ],
        )
        self.setUpBasicNumber(
            TEMPLIMIT_DPS,
            self.entities.get("number_room_temperature_limit"),
            device_class=NumberDeviceClass.TEMPERATURE,
            min=10.0,
            max=40.0,
            step=0.5,
            scale=10,
            unit=UnitOfTemperature.CELSIUS,
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": CURRENTTEMP_DPS,
                    "name": "sensor_room_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "unit": UnitOfTemperature.CELSIUS,
                    "testdata": (195, 19.5),
                },
                {
                    "dps": FLOORTEMP_DPS,
                    "name": "sensor_floor_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": STATE_CLASS_MEASUREMENT,
                    "unit": UnitOfTemperature.CELSIUS,
                    "testdata": (214, 21.4),
                },
                {
                    "dps": ENERGY_DPS,
                    "name": "sensor_energy",
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "testdata": (1234, 123.4),
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_screen_lock",
                "number_room_temperature_limit",
                "select_auto_schedule",
                "select_temperature_sensor",
                "select_temperature_unit",
            ],
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE,
        )

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = False
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.CELSIUS,
        )
        self.assertEqual(self.subject.target_temperature_step, 0.5)

        self.dps[UNIT_DPS] = True
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.FAHRENHEIT,
        )
        self.assertEqual(self.subject.target_temperature_step, 3.0)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 385
        self.assertEqual(self.subject.current_temperature, 38.5)

    def test_farenheit(self):
        self.dps[UNIT_DPS] = True
        # these seem suspicious, but are the values provided by the device
        # owner in the config.  Basically in C they translate to:
        # Setting    C            F
        # min temp   5           12F = -11C
        # max temp  40           75F = 24C
        # temp step  0.5          3F = 2C
        # It seems more likely that it should be 40 - 100 with step 1
        # (or in the config, 400 - 1000, step 10, scale 10)
        self.assertEqual(self.subject.min_temp, 12.0)
        self.assertEqual(self.subject.max_temp, 75.0)
        self.assertEqual(self.subject.target_temperature_step, 3.0)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = False
        self.dps[HVACMODE_DPS] = "Smart"
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

        self.dps[POWER_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)

        self.dps[HVACMODE_DPS] = "Manual"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "Anti_frozen"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.AUTO,
                HVACMode.COOL,
                HVACMode.HEAT,
                HVACMode.OFF,
            ],
        )

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError,
            f"temperature \\(4.5\\) must be between 5.0 and 40.0",
        ):
            await self.subject.async_set_target_temperature(4.5)
        with self.assertRaisesRegex(
            ValueError,
            f"temperature \\(41\\) must be between 5.0 and 40.0",
        ):
            await self.subject.async_set_target_temperature(41)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN104_DPS] = 104
        self.dps[UNKNOWN109_DPS] = True
        self.dps[UNKNOWN112_DPS] = 112
        self.dps[UNKNOWN113_DPS] = 113
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_104": 104,
                "unknown_109": True,
                "unknown_112": 112,
                "unknown_113": 113,
            },
        )

    def test_multi_sensor_extra_state_attributes(self):
        self.dps[CALIB_DPS] = 321
        self.assertEqual(
            self.multiSensor["sensor_energy"].extra_state_attributes,
            {"calibration": 321},
        )

    def test_icons(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")
