from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_COMFORT,
    PRESET_ECO,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import EUROM_601_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "6"
ERROR_DPS = "13"


class TestEurom601Heater(BasicBinarySensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("eurom_601_heater.yaml", EUROM_601_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=DEVICE_CLASS_PROBLEM,
            testdata=(1, 0),
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

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 15)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 24}
        ):
            await self.subject.async_set_temperature(temperature=24)

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called()

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25},
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 23}
        ):
            await self.subject.async_set_target_temperature(22.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(14\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(14)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(36\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

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

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [PRESET_COMFORT, PRESET_ECO],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = True
        self.assertEqual(self.subject.preset_mode, PRESET_ECO)

        self.dps[PRESET_DPS] = False
        self.assertEqual(self.subject.preset_mode, PRESET_COMFORT)

    async def test_set_preset_more_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: True}
        ):
            await self.subject.async_set_preset_mode(PRESET_ECO)

    async def test_set_preset_more_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: False}
        ):
            await self.subject.async_set_preset_mode(PRESET_COMFORT)
