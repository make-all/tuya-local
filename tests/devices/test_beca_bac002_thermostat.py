from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    PRESET_COMFORT,
    PRESET_ECO,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE, TEMP_CELSIUS

from ..const import BECA_BAC002_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.select import BasicSelectTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
CURRENTTEMP_DPS = "2"
TEMPERATURE_DPS = "3"
HVACMODE_DPS = "4"
PRESET_DPS = "5"
LOCK_DPS = "6"
INSTALL_DPS = "102"
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
            INSTALL_DPS,
            self.entities.get("select_installation"),
            {
                "0": "Cooling",
                "1": "Heating",
                "2": "Fan",
            },
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE,
        )

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

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
        self.dps[INSTALL_DPS] = "0"
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)
        self.dps[INSTALL_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)
        self.dps[INSTALL_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)
        self.dps[HVACMODE_DPS] = "0"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_AUTO)
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)
        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.dps[INSTALL_DPS] = "1"
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_AUTO,
                HVAC_MODE_HEAT,
                HVAC_MODE_OFF,
            ],
        )

    async def test_set_hvac_mode_to_auto(self):
        self.dps[INSTALL_DPS] = "1"
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True, HVACMODE_DPS: "0"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_AUTO)

    async def test_set_hvac_mode_to_heat(self):
        self.dps[INSTALL_DPS] = "1"
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True, HVACMODE_DPS: "1"},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_set_hvac_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

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

    def test_device_state_attribures(self):
        self.assertEqual(self.subject.device_state_attributes, {})
