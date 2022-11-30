from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from ..const import HYUNDAI_SAHARA_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.lock import BasicLockTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
HUMIDITY_DPS = "2"
FAN_DPS = "4"
CURRENTHUMID_DPS = "6"
CURRENTTEMP_DPS = "7"
MODE_DPS = "14"
LOCK_DPS = "16"
ERROR_DPS = "19"


class TestHyundaiSaharaDehumidifier(
    BasicBinarySensorTests,
    BasicLockTests,
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("hyundai_sahara_dehumidifier.yaml", HYUNDAI_SAHARA_PAYLOAD)
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.fan = self.entities.get("fan")
        self.setUpBasicLock(
            LOCK_DPS,
            self.entities.get("lock_child_lock"),
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_tank"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
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
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ]
        )
        self.mark_secondary(["binary_sensor_tank", "lock_child_lock"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            HumidifierEntityFeature.MODES,
        )
        self.assertEqual(
            self.fan.supported_features,
            FanEntityFeature.SET_SPEED,
        )

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = False
        self.dps[ERROR_DPS] = 0
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[MODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:power-sleep")

        self.dps[ERROR_DPS] = 1
        self.assertEqual(self.subject.icon, "mdi:cup-water")

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
                "Sleep",
            ],
        )

    def test_mode(self):
        self.dps[MODE_DPS] = False
        self.assertEqual(self.subject.mode, "Normal")
        self.dps[MODE_DPS] = True
        self.assertEqual(self.subject.mode, "Sleep")

    async def test_set_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: False,
            },
        ):
            await self.subject.async_set_mode("Normal")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: True,
            },
        ):
            await self.subject.async_set_mode("Sleep")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_fan_speed_steps(self):
        self.assertEqual(self.fan.speed_count, 2)

    def test_fan_speed(self):
        self.dps[FAN_DPS] = "low"
        self.assertEqual(self.fan.percentage, 50)
        self.dps[FAN_DPS] = "high"
        self.assertEqual(self.fan.percentage, 100)

    async def test_fan_set_speed_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                FAN_DPS: "low",
            },
        ):
            await self.fan.async_set_percentage(50)

    async def test_fan_set_speed_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                FAN_DPS: "high",
            },
        ):
            await self.fan.async_set_percentage(100)
