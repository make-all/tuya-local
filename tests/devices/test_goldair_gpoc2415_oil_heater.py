from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import UnitOfTemperature

from ..const import GOLDAIR_GPOC2415_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESETMODE_DPS = "5"
CHILDLOCK_DPS = "7"
HVACACTION_DPS = "11"
COUNTDOWN_DPS = "20"
FAULT_DPS = "21"
SOUND_DPS = "101"
DESTINE_TIME_DPS = "102"
FIXED_TIME_DPS = "103"


class TestGoldairGPOC2415OilHeater(
    BasicBinarySensorTests,
    BasicLockTests,
    BasicNumberTests,
    BasicSensorTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "goldair_gpoc2415_oil_heater.yaml", GOLDAIR_GPOC2415_PAYLOAD
        )
        self.subject = self.entities.get("climate_heater")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5.0,
            max=35.0,
        )
        self.setUpBasicLock(CHILDLOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSensor(
            COUNTDOWN_DPS,
            self.entities.get("sensor_countdown_remaining"),
            testdata=(60, 60),
            unit="min",
        )
        self.setUpBasicBinarySensor(
            FAULT_DPS,
            self.entities.get("binary_sensor_sensor_fault"),
            testdata=(
                1,
                0,
            ),  # 1 = fault detected = sensor on, 0 = no fault = sensor off
            device_class="problem",
        )
        self.setUpBasicSwitch(
            SOUND_DPS,
            self.entities.get("switch_sound"),
            testdata=(
                False,
                True,
            ),  # inverted: false = sound on = switch on, true = no sound = switch off
        )
        self.setUpBasicNumber(
            DESTINE_TIME_DPS,
            self.entities.get("number_preheat_timer"),
            max=24,
            min=0,
            unit="h",
        )
        self.setUpBasicNumber(
            FIXED_TIME_DPS,
            self.entities.get("number_auto_shutoff"),
            max=24,
            min=0,
            unit="h",
        )
        # Track secondary entities for category test
        self.secondary_category = [
            "lock_child_lock",
            "sensor_countdown_remaining",
            "binary_sensor_sensor_fault",
            "switch_sound",
            "number_preheat_timer",
            "number_auto_shutoff",
        ]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF,
        )

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

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
        self.dps[PRESETMODE_DPS] = "level_0"
        self.assertEqual(self.subject.preset_mode, "eco")

        self.dps[PRESETMODE_DPS] = "level_1"
        self.assertEqual(self.subject.preset_mode, "low")

        self.dps[PRESETMODE_DPS] = "level_2"
        self.assertEqual(self.subject.preset_mode, "medium")

        self.dps[PRESETMODE_DPS] = "level_3"
        self.assertEqual(self.subject.preset_mode, "high")

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["eco", "low", "medium", "high"],
        )

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESETMODE_DPS: "level_0"},
        ):
            await self.subject.async_set_preset_mode("eco")

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESETMODE_DPS: "level_1"},
        ):
            await self.subject.async_set_preset_mode("low")

    async def test_set_preset_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESETMODE_DPS: "level_2"},
        ):
            await self.subject.async_set_preset_mode("medium")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESETMODE_DPS: "level_3"},
        ):
            await self.subject.async_set_preset_mode("high")

    def test_hvac_action(self):
        self.dps[HVACACTION_DPS] = "warm"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

        self.dps[HVACACTION_DPS] = "stop"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)

        self.dps[HVACACTION_DPS] = "standby"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)
