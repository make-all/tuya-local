from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    TIME_HOURS,
    TEMP_CELSIUS,
)
from ..const import JJPRO_JPD01_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import MultiSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
MODE_DPS = "2"
HUMIDITY_DPS = "4"
ANION_DPS = "5"
FAN_DPS = "6"
ERROR_DPS = "11"
TIMER_DPS = "12"
UNKNOWN101_DPS = "101"
SLEEP_DPS = "102"
CURRENTTEMP_DPS = "103"
CURRENTHUMID_DPS = "104"
DEFROST_DPS = "105"


class TestJJProJPD01Dehumidifier(
    BasicNumberTests,
    MultiBinarySensorTests,
    MultiSensorTests,
    MultiSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("jjpro_jpd01_dehumidifier.yaml", JJPRO_JPD01_PAYLOAD)
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.fan = self.entities.get("fan")
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=24,
            unit=TIME_HOURS,
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "dps": ERROR_DPS,
                    "name": "binary_sensor_tank",
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (1, 0),
                },
                {
                    "dps": DEFROST_DPS,
                    "name": "binary_sensor_defrost",
                    "device_class": BinarySensorDeviceClass.COLD,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": CURRENTHUMID_DPS,
                    "name": "sensor_current_humidity",
                    "device_class": SensorDeviceClass.HUMIDITY,
                    "state_class": "measurement",
                    "unit": PERCENTAGE,
                },
                {
                    "dps": CURRENTTEMP_DPS,
                    "name": "sensor_current_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": "measurement",
                    "unit": TEMP_CELSIUS,
                },
            ]
        )
        self.setUpMultiSwitch(
            [
                {
                    "dps": SLEEP_DPS,
                    "name": "switch_sleep",
                },
                {
                    "dps": ANION_DPS,
                    "name": "switch_ionizer",
                },
            ]
        )
        self.mark_secondary(
            [
                "binary_sensor_tank",
                "binary_sensor_defrost",
                "number_timer",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, HumidifierEntityFeature.MODES)
        self.assertEqual(self.fan.supported_features, FanEntityFeature.SET_SPEED)

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[SWITCH_DPS] = True
        self.dps[ANION_DPS] = False
        self.dps[SLEEP_DPS] = False
        self.dps[DEFROST_DPS] = False
        self.dps[MODE_DPS] = "0"
        self.assertEqual(self.subject.icon, "mdi:water-outline")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")
        self.dps[MODE_DPS] = "1"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:water-plus-outline")
        self.dps[MODE_DPS] = "2"
        self.assertEqual(self.subject.icon, "mdi:tshirt-crew-outline")
        self.dps[MODE_DPS] = "3"
        self.assertEqual(self.subject.icon, "mdi:tailwind")
        self.dps[ERROR_DPS] = 8
        self.assertEqual(self.subject.icon, "mdi:cup-water")
        self.dps[DEFROST_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:cup-water")
        self.dps[ERROR_DPS] = 0
        self.assertEqual(self.subject.icon, "mdi:snowflake-melt")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    async def test_fan_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.fan.async_turn_on()

    async def test_fan_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.fan.async_turn_off()

    def test_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            [
                "Normal",
                "Continuous",
                "Strong",
                "Ventilation",
            ],
        )

    def test_mode(self):
        self.dps[MODE_DPS] = "0"
        self.assertEqual(self.subject.mode, "Normal")
        self.dps[MODE_DPS] = "1"
        self.assertEqual(self.subject.mode, "Continuous")
        self.dps[MODE_DPS] = "2"
        self.assertEqual(self.subject.mode, "Strong")
        self.dps[MODE_DPS] = "3"
        self.assertEqual(self.subject.mode, "Ventilation")

    async def test_set_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "0",
            },
        ):
            await self.subject.async_set_mode("Normal")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_continuous(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "1",
            },
        ):
            await self.subject.async_set_mode("Continuous")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_strong(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "2",
            },
        ):
            await self.subject.async_set_mode("Strong")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_ventilation(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "3",
            },
        ):
            await self.subject.async_set_mode("Ventilation")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_fan_speed_steps(self):
        self.assertEqual(self.fan.speed_count, 2)

    def test_fan_speed(self):
        self.dps[FAN_DPS] = "1"
        self.assertEqual(self.fan.percentage, 50)
        self.dps[FAN_DPS] = "3"

    async def test_fan_set_speed_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                FAN_DPS: "1",
            },
        ):
            await self.fan.async_set_percentage(50)

    async def test_fan_set_speed_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                FAN_DPS: "3",
            },
        ):
            await self.fan.async_set_percentage(100)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN101_DPS] = True
        self.dps[ERROR_DPS] = 5
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": 5,
                "unknown_101": True,
            },
        )
        self.assertEqual(self.fan.extra_state_attributes, {})
