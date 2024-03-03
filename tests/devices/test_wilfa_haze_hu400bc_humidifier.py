from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.components.humidifier.const import MODE_AUTO, MODE_NORMAL
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from ..const import WILFA_HAZE_HUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.light import MultiLightTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
LIGHT_DPS = "5"
SOUND_DPS = "8"
CURRENTTEMP_DPS = "10"
HUMIDITY_DPS = "13"
CURRENTHUMID_DPS = "14"
SLEEP_DPS = "16"
UNIT_DPS = "18"
TIMER_DPS = "19"
UNKNOWN20_DPS = "20"
ERROR_DPS = "22"
FAN_DPS = "23"
PRESET_DPS = "24"
CLEAN_DPS = "26"
IONIZER_DPS = "35"


class TestWilfaHazeHumidifier(
    BasicBinarySensorTests,
    MultiLightTests,
    MultiSelectTests,
    MultiSensorTests,
    MultiSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "wilfa_haze_hu400bc_humidifier.yaml", WILFA_HAZE_HUMIDIFIER_PAYLOAD
        )
        self.subject = self.entities.get("humidifier_humidifier")
        self.fan = self.entities.get("fan")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_tank_empty"),
            testdata=(1, 0),
        )
        self.setUpMultiLights(
            [
                {
                    "dps": SLEEP_DPS,
                    "name": "light_display",
                    "testdata": (False, True),
                },
                {
                    "dps": LIGHT_DPS,
                    "name": "light_mood",
                },
            ],
        )
        self.setUpMultiSelect(
            [
                {
                    "dps": TIMER_DPS,
                    "name": "select_timer",
                    "options": {
                        "cancel": "Off",
                        "1": "1 hour",
                        "2": "2 hours",
                        "3": "3 hours",
                        "4": "4 hours",
                        "5": "5 hours",
                        "6": "6 hours",
                        "7": "7 hours",
                        "8": "8 hours",
                        "9": "9 hours",
                        "10": "10 hours",
                        "11": "11 hours",
                        "12": "12 hours",
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
        self.setUpMultiSensors(
            [
                {
                    "dps": CURRENTTEMP_DPS,
                    "name": "sensor_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": "measurement",
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "dps": CURRENTHUMID_DPS,
                    "name": "sensor_current_humidity",
                    "device_class": SensorDeviceClass.HUMIDITY,
                    "state_class": "measurement",
                    "unit": PERCENTAGE,
                },
            ]
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": SOUND_DPS,
                    "name": "switch_sound",
                },
                {
                    "dps": CLEAN_DPS,
                    "name": "switch_air_clean",
                },
                {
                    "dps": IONIZER_DPS,
                    "name": "switch_ionizer",
                },
            ]
        )
        self.mark_secondary(
            [
                "binary_sensor_tank_empty",
                "light_display",
                "light_mood",
                "select_temperature_unit",
                "select_timer",
                "sensor_current_humidity",
                "switch_air_clean",
                "switch_ionizer",
                "switch_sound",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, HumidifierEntityFeature.MODES)

    def test_icons(self):
        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 90)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    def test_available_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            [MODE_AUTO, MODE_NORMAL],
        )

    def test_mode(self):
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.mode, MODE_AUTO)
        self.dps[PRESET_DPS] = "humidity"
        self.assertEqual(self.subject.mode, MODE_NORMAL)

    async def test_set_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "auto"}
        ):
            await self.subject.async_set_mode(MODE_AUTO)

    async def test_set_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "humidity"}
        ):
            await self.subject.async_set_mode(MODE_NORMAL)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN20_DPS] = 20
        self.dps[ERROR_DPS] = 22
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"unknown_20": 20, "error": 22},
        )
