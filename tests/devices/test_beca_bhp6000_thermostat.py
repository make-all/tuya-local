from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE, TEMP_CELSIUS, TEMP_FAHRENHEIT

from ..const import BECA_BHP6000_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

LIGHT_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
HVACMODE_DPS = "5"
FAN_DPS = "6"
LOCK_DPS = "7"


class TestBecaBHP6000Thermostat(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("beca_bhp6000_thermostat_f.yaml", BECA_BHP6000_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.light = self.entities.get("light")
        self.lock = self.entities.get("lock")

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE,
        )

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 40)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 95)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 80}
        ):
            await self.subject.async_set_temperature(temperature=80)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(self.subject._device, {PRESET_DPS: 1}):
            await self.subject.async_set_temperature(preset_mode="Schedule")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 78,
                PRESET_DPS: 4,
            },
        ):
            await self.subject.async_set_temperature(
                temperature=78, preset_mode="Holiday Hold"
            )

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 75},
        ):
            await self.subject.async_set_target_temperature(75)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 78}
        ):
            await self.subject.async_set_target_temperature(77.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(39\\) must be between 40 and 95"
        ):
            await self.subject.async_set_target_temperature(39)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(96\\) must be between 40 and 95"
        ):
            await self.subject.async_set_target_temperature(96)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 70
        self.assertEqual(self.subject.current_temperature, 70)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)

        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = "3"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = "4"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT_COOL)

        self.dps[HVACMODE_DPS] = "5"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_AUTO)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_OFF,
                HVAC_MODE_HEAT,
                HVAC_MODE_HEAT_COOL,
                HVAC_MODE_COOL,
                HVAC_MODE_AUTO,
            ],
        )

    def test_fan_mode(self):
        self.dps[FAN_DPS] = False
        self.assertEqual(self.subject.fan_mode, "auto")
        self.dps[FAN_DPS] = True
        self.assertEqual(self.subject.fan_mode, "on")

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            [
                "auto",
                "on",
            ],
        )

    async def test_set_fan_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: False},
        ):
            await self.subject.async_set_fan_mode("auto")

    async def test_set_fan_mode_to_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: True},
        ):
            await self.subject.async_set_fan_mode("on")

    def test_device_state_attribures(self):
        self.assertEqual(self.subject.device_state_attributes, {})
        self.assertEqual(self.light.device_state_attributes, {})
        self.assertEqual(self.lock.device_state_attributes, {})

    def test_icons(self):
        self.dps[HVACMODE_DPS] = 1
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = 2
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = 3
        self.assertEqual(self.subject.icon, "mdi:hvac-off")
        self.dps[HVACMODE_DPS] = 4
        self.assertEqual(self.subject.icon, "mdi:fire-alert")
        self.dps[HVACMODE_DPS] = 5
        self.assertEqual(self.subject.icon, "mdi:hvac")

        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-on")
        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-off")


class TestBecaBHP6000ThermostatC(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("beca_bhp6000_thermostat_c.yaml", BECA_BHP6000_PAYLOAD)
        self.subject = self.entities.get("climate")

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)
