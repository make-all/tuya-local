from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.components.humidifier.const import MODE_AUTO, MODE_NORMAL, MODE_SLEEP
from homeassistant.components.sensor import SensorDeviceClass

from ..const import EANONS_HUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

FANMODE_DPS = "2"
TIMERHR_DPS = "3"
TIMER_DPS = "4"
ERROR_DPS = "9"
HVACMODE_DPS = "10"
PRESET_DPS = "12"
HUMIDITY_DPS = "15"
CURRENTHUMID_DPS = "16"
SWITCH_DPS = "22"


class TestEanonsHumidifier(
    BasicBinarySensorTests,
    BasicSelectTests,
    BasicSensorTests,
    BasicSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("eanons_humidifier.yaml", EANONS_HUMIDIFIER_PAYLOAD)
        self.subject = self.entities.get("humidifier_humidifier")
        self.setUpSwitchable(HVACMODE_DPS, self.subject)
        self.fan = self.entities.get("fan_intensity")
        self.setUpBasicSwitch(SWITCH_DPS, self.entities.get("switch_uv_sterilization"))
        self.setUpBasicSelect(
            TIMERHR_DPS,
            self.entities.get("select_timer"),
            {
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
        )
        self.setUpBasicSensor(
            TIMER_DPS,
            self.entities.get("sensor_timer"),
            unit="min",
            device_class=SensorDeviceClass.DURATION,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_tank"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["select_timer", "sensor_timer", "binary_sensor_tank"])

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, HumidifierEntityFeature.MODES)
        self.assertEqual(self.fan.supported_features, FanEntityFeature.SET_SPEED)

    def test_icon_is_humidifier(self):
        """Test that the icon is as expected."""
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

    def test_current_humidity(self):
        self.dps[CURRENTHUMID_DPS] = 75
        self.assertEqual(self.subject.current_humidity, 75)

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 40)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 90)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    async def test_fan_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.fan.async_turn_on()

    async def test_fan_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.fan.async_turn_off()

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.subject.mode, MODE_SLEEP)

        self.dps[PRESET_DPS] = "humidity"
        self.assertEqual(self.subject.mode, MODE_AUTO)

        self.dps[PRESET_DPS] = "work"
        self.assertEqual(self.subject.mode, MODE_NORMAL)

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            [MODE_NORMAL, MODE_SLEEP, MODE_AUTO],
        )

    async def test_set_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "humidity",
            },
        ):
            await self.subject.async_set_mode(MODE_AUTO)
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "sleep",
            },
        ):
            await self.subject.async_set_mode(MODE_SLEEP)
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "work",
            },
        ):
            await self.subject.async_set_mode(MODE_NORMAL)
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 0
        self.dps[TIMERHR_DPS] = "cancel"
        self.dps[TIMER_DPS] = 0
        self.dps[FANMODE_DPS] = "middle"

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": "OK",
                "timer_hr": "cancel",
                "timer_min": 0,
            },
        )

    def test_fan_speed(self):
        self.dps[FANMODE_DPS] = "small"
        self.assertEqual(self.fan.percentage, 33)

        self.dps[FANMODE_DPS] = "middle"
        self.assertEqual(self.fan.percentage, 67)

        self.dps[FANMODE_DPS] = "large"
        self.assertEqual(self.fan.percentage, 100)

    def test_fan_speed_count(self):
        self.assertEqual(self.fan.speed_count, 3)

    def test_fan_percentage_step(self):
        self.assertAlmostEqual(self.fan.percentage_step, 33, 0)

    async def test_fan_set_speed(self):
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "small"},
        ):
            await self.fan.async_set_percentage(33)

    async def test_fan_set_speed_snaps(self):
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "middle"},
        ):
            await self.fan.async_set_percentage(60)
