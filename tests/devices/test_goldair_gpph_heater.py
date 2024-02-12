from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    PRECISION_WHOLE,
    UnitOfTemperature,
    UnitOfTime,
)

from ..const import GPPH_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.light import BasicLightTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
LOCK_DPS = "6"
ERROR_DPS = "12"
POWERLEVEL_DPS = "101"
TIMER_DPS = "102"
TIMERACT_DPS = "103"
LIGHT_DPS = "104"
SWING_DPS = "105"
ECOTEMP_DPS = "106"


class TestGoldairHeater(
    BasicBinarySensorTests,
    BasicLightTests,
    BasicLockTests,
    BasicNumberTests,
    BasicSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("goldair_gpph_heater.yaml", GPPH_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5.0,
            max=35.0,
        )
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440,
            step=60,
            unit=UnitOfTime.MINUTES,
        )
        self.setUpBasicSensor(
            POWERLEVEL_DPS,
            self.entities.get("sensor_power_level"),
            unit=PERCENTAGE,
            device_class=SensorDeviceClass.POWER_FACTOR,
            testdata=("2", 40),
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(
            [
                "light_display",
                "lock_child_lock",
                "number_timer",
                "sensor_power_level",
                "binary_sensor_error",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.SWING_MODE
            ),
        )

    def test_translation_key(self):
        self.assertEqual(self.subject.translation_key, "swing_as_powerlevel")

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

        self.dps[HVACMODE_DPS] = True
        self.dps[POWERLEVEL_DPS] = "stop"
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.CELSIUS,
        )

    def test_precision(self):
        self.assertEqual(self.subject.precision, PRECISION_WHOLE)

    def test_target_temperature_in_eco_and_af_modes(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.dps[ECOTEMP_DPS] = 15

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.target_temperature, 15)

        self.dps[PRESET_DPS] = "AF"
        self.assertIs(self.subject.target_temperature, None)

    def test_minimum_temperature(self):
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.min_temp, 5.0)

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.min_temp, 5.0)

        self.dps[PRESET_DPS] = "AF"
        self.assertEqual(self.subject.min_temp, 5.0)

    def test_maximum_target_temperature(self):
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.max_temp, 35.0)

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.max_temp, 21.0)

        self.dps[PRESET_DPS] = "AF"
        self.assertEqual(self.subject.max_temp, 5.0)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "C"}
        ):
            await self.subject.async_set_temperature(preset_mode="comfort")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 25,
                PRESET_DPS: "C",
            },
        ):
            await self.subject.async_set_temperature(
                temperature=25, preset_mode="comfort"
            )

    async def test_set_target_temperature_in_eco_mode(self):
        self.dps[PRESET_DPS] = "ECO"

        async with assert_device_properties_set(
            self.subject._device, {ECOTEMP_DPS: 15}
        ):
            await self.subject.async_set_target_temperature(15)

    async def test_set_target_temperature_fails_outside_valid_range_in_eco(
        self,
    ):
        self.dps[PRESET_DPS] = "ECO"

        with self.assertRaisesRegex(
            ValueError, "eco_temperature \\(4\\) must be between 5.0 and 21.0"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "eco_temperature \\(22\\) must be between 5.0 and 21.0"
        ):
            await self.subject.async_set_target_temperature(22)

    async def test_set_target_temperature_fails_in_anti_freeze(self):
        self.dps[PRESET_DPS] = "AF"

        with self.assertRaisesRegex(
            AttributeError, "temperature cannot be set at this time"
        ):
            await self.subject.async_set_target_temperature(25)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_humidity_unsupported(self):
        self.assertIsNone(self.subject.min_humidity)
        self.assertIsNone(self.subject.max_humidity)
        self.assertIsNone(self.subject.current_humidity)
        with self.assertRaises(NotImplementedError):
            self.subject.target_humidity

    async def test_set_humidity_unsupported(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_set_humidity(50)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.OFF, HVACMode.HEAT],
        )

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

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "C"
        self.assertEqual(self.subject.preset_mode, "comfort")

        self.dps[PRESET_DPS] = "ECO"
        self.assertEqual(self.subject.preset_mode, "eco")

        self.dps[PRESET_DPS] = "AF"
        self.assertEqual(self.subject.preset_mode, "away")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["comfort", "eco", "away"],
        )

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "C"},
        ):
            await self.subject.async_set_preset_mode("comfort")

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "ECO"},
        ):
            await self.subject.async_set_preset_mode("eco")

    async def test_set_preset_mode_to_anti_freeze(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "AF"},
        ):
            await self.subject.async_set_preset_mode("away")

    def test_power_level_returns_user_power_level(self):
        self.dps[SWING_DPS] = "user"

        self.dps[POWERLEVEL_DPS] = "stop"
        self.assertEqual(self.subject.swing_mode, "stop")

        self.dps[POWERLEVEL_DPS] = "3"
        self.assertEqual(self.subject.swing_mode, "3")

    def test_non_user_swing_mode(self):
        self.dps[SWING_DPS] = "stop"
        self.assertEqual(self.subject.swing_mode, "stop")

        self.dps[SWING_DPS] = "auto"
        self.assertEqual(self.subject.swing_mode, "auto")

        self.dps[SWING_DPS] = None
        self.assertIs(self.subject.swing_mode, None)

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            ["stop", "1", "2", "3", "4", "5", "auto"],
        )

    async def test_set_power_level_to_stop(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWERLEVEL_DPS: "stop", SWING_DPS: "stop"},
        ):
            await self.subject.async_set_swing_mode("stop")

    async def test_set_swing_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: "auto"},
        ):
            await self.subject.async_set_swing_mode("auto")

    async def test_set_power_level_to_numeric_value(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: "user", POWERLEVEL_DPS: "3"},
        ):
            await self.subject.async_set_swing_mode("3")

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = "something"
        self.dps[TIMER_DPS] = 5
        self.dps[TIMERACT_DPS] = True
        self.dps[POWERLEVEL_DPS] = 4

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": "something",
                "timer": 5,
                "timer_mode": True,
                "power_level": "4",
            },
        )

    def test_light_icon(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")
