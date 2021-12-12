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
from ..mixins.climate import TargetTemperatureTests
from ..mixins.light import BasicLightTests
from ..mixins.lock import BasicLockTests
from .base_device_tests import TuyaDeviceTestCase

LIGHT_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
HVACMODE_DPS = "5"
FAN_DPS = "6"
LOCK_DPS = "7"


class TestBecaBHP6000Thermostat(
    BasicLightTests,
    BasicLockTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("beca_bhp6000_thermostat_f.yaml", BECA_BHP6000_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=40,
            max=95,
        )
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.mark_secondary(["light_display", "lock_child_lock"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE,
        )

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, TEMP_FAHRENHEIT)

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

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})

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
        self.assertEqual(self.basicLight.icon, "mdi:led-on")
        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")


class TestBecaBHP6000ThermostatC(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("beca_bhp6000_thermostat_c.yaml", BECA_BHP6000_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.mark_secondary(["light_display", "lock_child_lock"])

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, TEMP_CELSIUS)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)
