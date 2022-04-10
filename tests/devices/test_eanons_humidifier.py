from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    FAN_HIGH,
    FAN_MEDIUM,
    FAN_LOW,
    HVAC_MODE_DRY,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
)
from homeassistant.components.fan import (
    SUPPORT_SET_SPEED,
)
from homeassistant.components.humidifier.const import (
    MODE_NORMAL,
    MODE_AUTO,
    MODE_SLEEP,
    SUPPORT_MODES,
)
from homeassistant.const import STATE_UNAVAILABLE

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
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(HVACMODE_DPS, self.subject)
        self.climate = self.entities.get("climate")
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
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_tank"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["select_timer", "sensor_timer", "binary_sensor_tank"])

    def test_supported_features(self):
        self.assertEqual(
            self.climate.supported_features,
            SUPPORT_TARGET_HUMIDITY | SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE,
        )
        self.assertEqual(self.subject.supported_features, SUPPORT_MODES)
        self.assertEqual(self.fan.supported_features, SUPPORT_SET_SPEED)

    def test_climate_icon_is_humidifier(self):
        """Test that the icon is as expected."""
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.climate.icon, "mdi:air-humidifier")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.climate.icon, "mdi:air-humidifier-off")

    def test_icon_is_humidifier(self):
        """Test that the icon is as expected."""
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

    def test_current_humidity(self):
        self.dps[CURRENTHUMID_DPS] = 47
        self.assertEqual(self.climate.current_humidity, 47)

    def test_min_target_humidity(self):
        self.assertEqual(self.climate.min_humidity, 40)
        self.assertEqual(self.subject.min_humidity, 40)

    def test_max_target_humidity(self):
        self.assertEqual(self.climate.max_humidity, 90)
        self.assertEqual(self.subject.max_humidity, 90)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.climate.target_humidity, 55)
        self.assertEqual(self.subject.target_humidity, 55)

    def test_climate_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.climate.hvac_mode, HVAC_MODE_DRY)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.climate.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.climate.hvac_mode, STATE_UNAVAILABLE)

    def test_climate_hvac_modes(self):
        self.assertCountEqual(self.climate.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_DRY])

    async def test_climate_turn_on(self):
        async with assert_device_properties_set(
            self.climate._device, {HVACMODE_DPS: True}
        ):
            await self.climate.async_set_hvac_mode(HVAC_MODE_DRY)

    async def test_climate_turn_off(self):
        async with assert_device_properties_set(
            self.climate._device, {HVACMODE_DPS: False}
        ):
            await self.climate.async_set_hvac_mode(HVAC_MODE_OFF)

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
        self.assertEqual(self.climate.preset_mode, MODE_SLEEP)
        self.assertEqual(self.subject.mode, MODE_SLEEP)

        self.dps[PRESET_DPS] = "humidity"
        self.assertEqual(self.climate.preset_mode, MODE_AUTO)
        self.assertEqual(self.subject.mode, MODE_AUTO)

        self.dps[PRESET_DPS] = "work"
        self.assertEqual(self.climate.preset_mode, MODE_NORMAL)
        self.assertEqual(self.subject.mode, MODE_NORMAL)

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.climate.preset_mode, None)
        self.assertEqual(self.subject.mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.climate.preset_modes,
            [MODE_NORMAL, MODE_SLEEP, MODE_AUTO],
        )
        self.assertCountEqual(
            self.subject.available_modes,
            [MODE_NORMAL, MODE_SLEEP, MODE_AUTO],
        )

    async def test_set_climate_preset_to_auto(self):
        async with assert_device_properties_set(
            self.climate._device,
            {
                PRESET_DPS: "humidity",
            },
        ):
            await self.climate.async_set_preset_mode(MODE_AUTO)
            self.climate._device.anticipate_property_value.assert_not_called()

    async def test_set_climate_preset_to_sleep(self):
        async with assert_device_properties_set(
            self.climate._device,
            {
                PRESET_DPS: "sleep",
            },
        ):
            await self.climate.async_set_preset_mode(MODE_SLEEP)
            self.climate._device.anticipate_property_value.assert_not_called()

    async def test_set_climate_preset_to_normal(self):
        async with assert_device_properties_set(
            self.climate._device,
            {
                PRESET_DPS: "work",
            },
        ):
            await self.climate.async_set_preset_mode(MODE_NORMAL)
            self.climate._device.anticipate_property_value.assert_not_called()

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

    def test_climate_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 0
        self.dps[TIMERHR_DPS] = "cancel"
        self.dps[TIMER_DPS] = 0
        self.assertDictEqual(
            self.climate.extra_state_attributes,
            {
                "error": "OK",
                "timer_hr": "cancel",
                "timer_min": 0,
            },
        )

        self.dps[ERROR_DPS] = 1
        self.dps[TIMERHR_DPS] = "1"
        self.dps[TIMER_DPS] = 60
        self.assertDictEqual(
            self.climate.extra_state_attributes,
            {
                "error": "Water Level Low",
                "timer_hr": "1",
                "timer_min": 60,
            },
        )

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 0
        self.dps[TIMERHR_DPS] = "cancel"
        self.dps[TIMER_DPS] = 0
        self.dps[CURRENTHUMID_DPS] = 50
        self.dps[FANMODE_DPS] = "middle"

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": "OK",
                "timer_hr": "cancel",
                "timer_min": 0,
                "current_humidity": 50,
            },
        )

    def test_fan_speed(self):
        self.dps[FANMODE_DPS] = "small"
        self.assertEqual(self.fan.percentage, 33)

        self.dps[FANMODE_DPS] = "middle"
        self.assertEqual(self.fan.percentage, 67)

        self.dps[FANMODE_DPS] = "large"
        self.assertEqual(self.fan.percentage, 100)

    def test_climate_fan_mode(self):
        self.dps[FANMODE_DPS] = "small"
        self.assertEqual(self.climate.fan_mode, FAN_LOW)

        self.dps[FANMODE_DPS] = "middle"
        self.assertEqual(self.climate.fan_mode, FAN_MEDIUM)

        self.dps[FANMODE_DPS] = "large"
        self.assertEqual(self.climate.fan_mode, FAN_HIGH)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    def test_fan_speed_count(self):
        self.assertEqual(self.fan.speed_count, 3)

    def test_fan_percentage_step(self):
        self.assertAlmostEqual(self.fan.percentage_step, 33, 0)

    def test_climate_fan_modes(self):
        self.assertCountEqual(
            self.climate.fan_modes,
            [FAN_LOW, FAN_MEDIUM, FAN_HIGH],
        )

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

    async def test_climate_set_fan_mode(self):
        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: "small"},
        ):
            await self.climate.async_set_fan_mode(FAN_LOW)
