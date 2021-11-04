from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    PRESET_AWAY,
    PRESET_HOME,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.lock import STATE_LOCKED, STATE_UNLOCKED
from homeassistant.const import STATE_UNAVAILABLE

from ..const import SASWELL_C16_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import BasicLockTests, TuyaDeviceTestCase

TEMPERATURE_DPS = "2"
PRESET_DPS = "3"
UNKNOWN4_DPS = "4"
CURRENTTEMP_DPS = "5"
FLOORTEMPLIMIT_DPS = "6"
INSTALL_DPS = "7"
FLOORTEMP_DPS = "8"
HVACMODE_DPS = "9"
ADAPTIVE_DPS = "10"
LOCK_DPS = "11"
SCHED_DPS = "12"
UNKNOWN14_DPS = "14"
UNKNOWN15_DPS = "15"
UNKNOWN17_DPS = "17"
UNKNOWN21_DPS = "21"
POWERRATING_DPS = "22"
UNKNOWN23_DPS = "23"
HVACACTION_DPS = "24"
UNKNOWN26_DPS = "26"


class TestSaswellC16Thermostat(BasicLockTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "saswell_c16_thermostat.yaml", SASWELL_C16_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        self.dps[PRESET_DPS] = "Smart"
        self.assertEqual(self.subject.icon, "mdi:home-thermometer")
        self.dps[PRESET_DPS] = "Manual"
        self.assertEqual(self.subject.icon, "mdi:cursor-pointer")
        self.dps[PRESET_DPS] = "Anti_frozen"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")

    def test_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            self.subject._device.temperature_unit,
        )

    def test_target_temperature(self):
        self.dps[TEMPERATURE_DPS] = 250
        self.assertEqual(self.subject.target_temperature, 25.0)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 0.5)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5.0)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 40.0)

    async def test_set_target_temperature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 240},
        ):
            await self.subject.async_set_target_temperature(24)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "temperature \\(4.5\\) must be between 5.0 and 40.0"
        ):
            await self.subject.async_set_target_temperature(4.5)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 250
        self.assertEqual(self.subject.current_temperature, 25.0)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_COOL)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVAC_MODE_COOL, HVAC_MODE_HEAT],
        )

    async def test_set_hvac_mode_cool(self):
        with self.assertRaises(TypeError):
            await self.subject.async_set_hvac_mode(HVAC_MODE_COOL)

    async def test_set_hvac_mode_heat(self):
        with self.assertRaises(TypeError):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    def test_hvac_action(self):
        self.dps[HVACACTION_DPS] = "Cooling"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_COOL)

        self.dps[HVACACTION_DPS] = "Heating"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_HEAT)

        self.dps[HVACACTION_DPS] = "Standby"
        self.assertEqual(self.subject.hvac_action, CURRENT_HVAC_IDLE)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "Smart"
        self.assertEqual(self.subject.preset_mode, PRESET_HOME)
        self.dps[PRESET_DPS] = "Manual"
        self.assertEqual(self.subject.preset_mode, "manual")
        self.dps[PRESET_DPS] = "Anti_frozen"
        self.assertEqual(self.subject.preset_mode, PRESET_AWAY)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [PRESET_HOME, PRESET_AWAY, "manual"],
        )

    async def test_set_preset_to_away(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Anti_frozen"},
        ):
            await self.subject.async_set_preset_mode(PRESET_AWAY)

    async def test_set_preset_to_home(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Smart"},
        ):
            await self.subject.async_set_preset_mode(PRESET_HOME)

    async def test_set_preset_to_manual(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "Manual"},
        ):
            await self.subject.async_set_preset_mode("manual")

    def test_device_state_attributes(self):
        self.dps[UNKNOWN4_DPS] = 4
        self.dps[FLOORTEMPLIMIT_DPS] = 355
        self.dps[INSTALL_DPS] = True
        self.dps[FLOORTEMP_DPS] = 251
        self.dps[ADAPTIVE_DPS] = False
        self.dps[SCHED_DPS] = "5_1_1"
        self.dps[UNKNOWN14_DPS] = 14
        self.dps[UNKNOWN15_DPS] = 15
        self.dps[UNKNOWN17_DPS] = 17
        self.dps[UNKNOWN21_DPS] = True
        self.dps[POWERRATING_DPS] = 2000
        self.dps[UNKNOWN23_DPS] = 23
        self.dps[UNKNOWN26_DPS] = 26

        self.assertDictEqual(
            self.subject.device_state_attributes,
            {
                "unknown_4": 4,
                "floor_temp_limit": 35.5,
                "installation": "Office",
                "floor_temperature": 25.1,
                "adaptive": False,
                "schedule": "5_1_1",
                "unknown_14": 14,
                "unknown_15": 15,
                "unknown_17": 17,
                "unknown_21": True,
                "power_rating": 2000,
                "unknown_23": 23,
                "unknown_26": 26,
            },
        )
