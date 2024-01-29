from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature

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
        self.setUpForConfig(
            "beca_bhp6000_thermostat_f.yaml",
            BECA_BHP6000_PAYLOAD,
        )
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
            (
                ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
            ),
        )

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.FAHRENHEIT,
        )

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: 1},
        ):
            await self.subject.async_set_temperature(preset_mode="program")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 78,
                PRESET_DPS: 4,
            },
        ):
            await self.subject.async_set_temperature(
                temperature=78,
                preset_mode="away",
            )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 70
        self.assertEqual(self.subject.current_temperature, 70)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

        self.dps[HVACMODE_DPS] = "2"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "3"
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

        self.dps[HVACMODE_DPS] = "4"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)

        self.dps[HVACMODE_DPS] = "5"
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.COOL,
                HVACMode.AUTO,
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
        self.setUpForConfig(
            "beca_bhp6000_thermostat_c.yaml",
            BECA_BHP6000_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.mark_secondary(["light_display", "lock_child_lock"])

    def test_temperature_unit_returns_configured_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            UnitOfTemperature.CELSIUS,
        )

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 5)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)
