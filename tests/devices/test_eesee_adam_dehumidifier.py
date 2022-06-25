from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE

from ..const import EESEE_ADAM_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.lock import BasicLockTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
HUMIDITY_DPS = "2"
MODE_DPS = "4"
FAN_DPS = "5"
LOCK_DPS = "14"
CURRENTHUMID_DPS = "16"
TIMER_DPS = "17"
ERROR_DPS = "19"


class TestEeseeAdamDehumidifier(
    BasicBinarySensorTests,
    BasicLockTests,
    BasicSelectTests,
    BasicSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("eesee_adam_dehumidifier.yaml", EESEE_ADAM_PAYLOAD)
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.fan = self.entities.get("fan")
        self.setUpBasicLock(
            LOCK_DPS,
            self.entities.get("lock_child_lock"),
        )
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities.get("select_timer"),
            {
                "cancel": "Off",
                "1h": "1 hour",
                "2h": "2 hours",
                "3h": "3 hours",
                "4h": "4 hours",
                "5h": "5 hours",
                "6h": "6 hours",
                "7h": "7 hours",
                "8h": "8 hours",
                "9h": "9 hours",
                "10h": "10 hours",
                "11h": "11 hours",
                "12h": "12 hours",
                "13h": "13 hours",
                "14h": "14 hours",
                "15h": "15 hours",
                "16h": "16 hours",
                "17h": "17 hours",
                "18h": "18 hours",
                "19h": "19 hours",
                "20h": "20 hours",
                "21h": "21 hours",
                "22h": "22 hours",
                "23h": "23 hours",
                "24h": "24 hours",
            },
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_tank"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpBasicSensor(
            CURRENTHUMID_DPS,
            self.entities.get("sensor_current_humidity"),
            device_class=SensorDeviceClass.HUMIDITY,
            state_class="measurement",
            unit=PERCENTAGE,
        )
        self.mark_secondary(["binary_sensor_tank", "lock_child_lock", "select_timer"])

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
        self.dps[MODE_DPS] = "manual"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[MODE_DPS] = "laundry"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:tshirt-crew-outline")

        self.dps[ERROR_DPS] = 1
        self.assertEqual(self.subject.icon, "mdi:cup-water")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 25)

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
                "Manual",
                "Dry clothes",
            ],
        )

    def test_mode(self):
        self.dps[MODE_DPS] = "manual"
        self.assertEqual(self.subject.mode, "Manual")
        self.dps[MODE_DPS] = "laundry"
        self.assertEqual(self.subject.mode, "Dry clothes")

    async def test_set_mode_to_manual(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "manual",
            },
        ):
            await self.subject.async_set_mode("Manual")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_clothes(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "laundry",
            },
        ):
            await self.subject.async_set_mode("Dry clothes")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_fan_speed_steps(self):
        self.assertEqual(self.fan.speed_count, 2)

    def test_fan_speed(self):
        self.dps[FAN_DPS] = "low"
        self.assertEqual(self.fan.percentage, 50)
        self.dps[FAN_DPS] = "high"
        self.assertEqual(self.fan.percentage, 100)
        self.dps[MODE_DPS] = "laundry"
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
