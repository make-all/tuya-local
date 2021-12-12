from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import GSH_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
ERROR_DPS = "12"


class TestAnderssonGSHHeater(TargetTemperatureTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("andersson_gsh_heater.yaml", GSH_HEATER_PAYLOAD)
        self.subject = self.entities["climate"]
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5,
            max=35,
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "low"}
        ):
            await self.subject.async_set_temperature(preset_mode="Low")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 26, PRESET_DPS: "high"}
        ):
            await self.subject.async_set_temperature(temperature=26, preset_mode="High")

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "low"
        self.assertEqual(self.subject.preset_mode, "Low")

        self.dps[PRESET_DPS] = "high"
        self.assertEqual(self.subject.preset_mode, "High")

        self.dps[PRESET_DPS] = "af"
        self.assertEqual(self.subject.preset_mode, "Anti-freeze")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["Low", "High", "Anti-freeze"])

    async def test_set_preset_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "low"},
        ):
            await self.subject.async_set_preset_mode("Low")

    async def test_set_preset_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "high"},
        ):
            await self.subject.async_set_preset_mode("High")

    async def test_set_preset_mode_to_af(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "af"},
        ):
            await self.subject.async_set_preset_mode("Anti-freeze")

    def test_error_state(self):
        # There are currently no known error states; update this as
        # they are discovered
        self.dps[ERROR_DPS] = "something"
        self.assertEqual(self.subject.extra_state_attributes, {"error": "something"})
        self.dps[ERROR_DPS] = "0"
        self.assertEqual(self.subject.extra_state_attributes, {"error": "OK"})
