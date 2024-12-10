from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_COMFORT,
    PRESET_ECO,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import PRECISION_TENTHS, UnitOfTemperature

from ..const import BECA_BAC002_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PROGRAM_DPS = "4"
PRESET_DPS = "5"
LOCK_DPS = "6"
HVACMODE_DPS = "102"
FAN_DPS = "103"


class TestBecaBAC002Thermostat(
    BasicLockTests,
    BasicSelectTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("beca_bac002_thermostat_c.yaml", BECA_BAC002_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5.0,
            max=35.0,
            scale=2,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSelect(
            PROGRAM_DPS,
            self.entities.get("select_schedule"),
            {
                "0": "program",
                "1": "manual",
            },
        )
        self.mark_secondary(["lock_child_lock"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TURN_ON
            ),
        )

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_precision(self):
        self.assertEqual(self.subject.precision, PRECISION_TENTHS)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: True}
        ):
            await self.subject.async_set_temperature(preset_mode=PRESET_ECO)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 58,
                PRESET_DPS: False,
            },
        ):
            await self.subject.async_set_temperature(
                temperature=29, preset_mode=PRESET_COMFORT
            )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 70
        self.assertEqual(self.subject.current_temperature, 35.0)

    def test_hvac_mode(self):
        self.dps[SWITCH_DPS] = True
        self.dps[HVACMODE_DPS] = "0"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.COOL,
                HVACMode.FAN_ONLY,
                HVACMode.HEAT,
                HVACMode.OFF,
            ],
        )

    async def test_set_hvac_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True, HVACMODE_DPS: "0"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True, HVACMODE_DPS: "1"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True, HVACMODE_DPS: "2"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.FAN_ONLY)

    async def test_set_hvac_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, [PRESET_COMFORT, PRESET_ECO])

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = False
        self.assertEqual(self.subject.preset_mode, PRESET_COMFORT)
        self.dps[PRESET_DPS] = True
        self.assertEqual(self.subject.preset_mode, PRESET_ECO)

    async def test_set_preset_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: False},
        ):
            await self.subject.async_set_preset_mode(PRESET_COMFORT)

    async def test_set_preset_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: True},
        ):
            await self.subject.async_set_preset_mode(PRESET_ECO)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "0"
        self.assertEqual(self.subject.fan_mode, FAN_AUTO)
        self.dps[FAN_DPS] = "1"
        self.assertEqual(self.subject.fan_mode, FAN_HIGH)
        self.dps[FAN_DPS] = "2"
        self.assertEqual(self.subject.fan_mode, FAN_MEDIUM)
        self.dps[FAN_DPS] = "3"
        self.assertEqual(self.subject.fan_mode, FAN_LOW)

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            [
                FAN_AUTO,
                FAN_LOW,
                FAN_MEDIUM,
                FAN_HIGH,
            ],
        )

    async def test_set_fan_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "0"},
        ):
            await self.subject.async_set_fan_mode(FAN_AUTO)

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "1"},
        ):
            await self.subject.async_set_fan_mode(FAN_HIGH)

    async def test_set_fan_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "2"},
        ):
            await self.subject.async_set_fan_mode(FAN_MEDIUM)

    async def test_set_fan_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "3"},
        ):
            await self.subject.async_set_fan_mode(FAN_LOW)

    def test_extra_state_attribures(self):
        self.assertEqual(self.subject.extra_state_attributes, {})
