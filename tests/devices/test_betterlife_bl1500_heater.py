from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import BETTERLIFE_BL1500_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
PRESET_DPS = "4"
LOCK_DPS = "7"
TIMER_DPS = "11"
COUNTDOWN_DPS = "12"


class TestBetterlifeBL1500Heater(
    BasicLockTests,
    BasicSelectTests,
    BasicSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("betterlife_bl1500_heater.yaml", BETTERLIFE_BL1500_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=15.0,
            max=30.0,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities.get("select_timer"),
            {
                "0": "Off",
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
            COUNTDOWN_DPS,
            self.entities.get("sensor_timer_countdown"),
            unit=UnitOfTime.MINUTES,
            device_class=SensorDeviceClass.DURATION,
        )
        self.mark_secondary(
            ["lock_child_lock", "select_timer", "sensor_timer_countdown"]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TURN_ON
            ),
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "2"}
        ):
            await self.subject.async_set_temperature(preset_mode="eco")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 26, PRESET_DPS: "1"}
        ):
            await self.subject.async_set_temperature(
                temperature=26, preset_mode="boost"
            )

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
        self.dps[PRESET_DPS] = "0"
        self.assertEqual(self.subject.preset_mode, "comfort")

        self.dps[PRESET_DPS] = "1"
        self.assertEqual(self.subject.preset_mode, "boost")

        self.dps[PRESET_DPS] = "2"
        self.assertEqual(self.subject.preset_mode, "eco")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["comfort", "boost", "eco"])

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "0"},
        ):
            await self.subject.async_set_preset_mode("comfort")

    async def test_set_preset_mode_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "1"},
        ):
            await self.subject.async_set_preset_mode("boost")

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "2"},
        ):
            await self.subject.async_set_preset_mode("eco")
