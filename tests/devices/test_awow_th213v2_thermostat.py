from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

from ..const import TH213V2_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
LOCK_DPS = "6"
ERROR_DPS = "12"
EXTERNTEMP_DPS = "101"
SENSOR_DPS = "102"
CALIBRATE_DPS = "103"
CALIBSWING_DPS = "104"
HVACACTION_DPS = "105"
UNKNOWN116_DPS = "116"


class TestAwowTH213v2Thermostat(
    BasicBinarySensorTests,
    BasicLockTests,
    BasicSelectTests,
    BasicSensorTests,
    MultiNumberTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("awow_th213v2_thermostat.yaml", TH213V2_THERMOSTAT_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5,
            max=30,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSensor(
            EXTERNTEMP_DPS,
            self.entities.get("sensor_external_temperature"),
            unit=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class="measurement",
        )
        self.setUpBasicSelect(
            SENSOR_DPS,
            self.entities.get("select_temperature_sensor"),
            {
                0: "Internal",
                1: "External",
                2: "Both",
            },
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpMultiNumber(
            [
                {
                    "name": "number_calibration_offset",
                    "dps": CALIBRATE_DPS,
                    "min": -9,
                    "max": 9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
                {
                    "name": "number_calibration_swing",
                    "dps": CALIBSWING_DPS,
                    "min": 1,
                    "max": 9,
                    "unit": UnitOfTemperature.CELSIUS,
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "select_temperature_sensor",
                "number_calibration_offset",
                "number_calibration_swing",
                "binary_sensor_error",
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
        self.dps[HVACACTION_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:thermometer")

        self.dps[HVACACTION_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:thermometer-off")

        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")

        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(self.subject._device, {PRESET_DPS: 2}):
            await self.subject.async_set_temperature(preset_mode="Away")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 25,
                PRESET_DPS: 3,
            },
        ):
            await self.subject.async_set_temperature(
                temperature=25, preset_mode="Smart"
            )

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
        self.dps[PRESET_DPS] = "1"
        self.assertEqual(self.subject.preset_mode, "Home")

        self.dps[PRESET_DPS] = "2"
        self.assertEqual(self.subject.preset_mode, "Away")

        self.dps[PRESET_DPS] = "3"
        self.assertEqual(self.subject.preset_mode, "Smart")

        self.dps[PRESET_DPS] = "4"
        self.assertEqual(self.subject.preset_mode, "Sleep")

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Home", "Away", "Smart", "Sleep"],
        )

    async def test_set_preset_mode_to_home(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: 1},
        ):
            await self.subject.async_set_preset_mode("Home")

    async def test_set_preset_mode_to_away(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: 2},
        ):
            await self.subject.async_set_preset_mode("Away")

    async def test_set_preset_mode_to_smart(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: 3},
        ):
            await self.subject.async_set_preset_mode("Smart")

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: 4},
        ):
            await self.subject.async_set_preset_mode("Sleep")

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = True
        self.dps[HVACACTION_DPS] = True
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

        self.dps[HVACACTION_DPS] = False
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_action, HVACAction.OFF)

    def test_extra_state_attributes(self):
        self.dps[ERROR_DPS] = 8
        self.dps[UNKNOWN116_DPS] = "116"

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "error": 8,
                "unknown_116": "116",
            },
        )
