from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_COMFORT,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import MOES_BHT002_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.lock import BasicLockTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
PRESET_DPS = "5"
LOCK_DPS = "6"
UNKNOWN104_DPS = "104"


class TestMoesBHT002Thermostat(BasicLockTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "moes_bht002_thermostat_c.yaml",
            MOES_BHT002_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE,
        )

    def test_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            self.subject._device.temperature_unit,
        )

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 50
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 0.5)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 41}
        ):
            await self.subject.async_set_temperature(temperature=20.5)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: True}
        ):
            await self.subject.async_set_temperature(preset_mode=PRESET_ECO)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 44,
                PRESET_DPS: False,
            },
        ):
            await self.subject.async_set_temperature(
                temperature=22, preset_mode=PRESET_COMFORT
            )

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 45},
        ):
            await self.subject.async_set_target_temperature(22.5)

    async def test_set_target_temperature_rounds_value_to_closest_half(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 35}
        ):
            await self.subject.async_set_target_temperature(17.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(4.5\\) must be between 5.0 and 35.0"
        ):
            await self.subject.async_set_target_temperature(4.5)

        with self.assertRaisesRegex(
            ValueError, "temperature \\(35.5\\) must be between 5.0 and 35.0"
        ):
            await self.subject.async_set_target_temperature(35.5)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 44
        self.assertEqual(self.subject.current_temperature, 22)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = False
        self.dps[HVACMODE_DPS] = "0"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[POWER_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_AUTO)

        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_HEAT,
                HVAC_MODE_AUTO,
                HVAC_MODE_OFF,
            ],
        )

    def test_device_state_attribures(self):
        self.dps[UNKNOWN104_DPS] = False

        self.assertDictEqual(
            self.subject.device_state_attributes,
            {"unknown_104": False},
        )

    def test_icons(self):
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")
