from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from ..const import ELECTRIQ_12WMINV_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.light import BasicLightTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
FAN_DPS = "5"
UNKNOWN8_DPS = "8"
UNKNOWN12_DPS = "12"
SWITCH_DPS = "101"
UNKNOWN102_DPS = "102"
UNKNOWN103_DPS = "103"
LIGHT_DPS = "104"
VSWING_DPS = "106"
HSWING_DPS = "107"
UNKNOWN108_DPS = "108"
UNKNOWN109_DPS = "109"
UNKNOWN110_DPS = "110"


class TestElectriq12WMINVHeatpump(
    BasicLightTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "electriq_12wminv_heatpump.yaml", ELECTRIQ_12WMINV_HEATPUMP_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16,
            max=32,
        )
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.setUpBasicSwitch(SWITCH_DPS, self.entities.get("switch_sleep"))
        self.mark_secondary(["light_display", "lock_child_lock"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.SWING_MODE
            ),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:hvac")
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.icon, "mdi:snowflake")
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "wet"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "wind"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

        self.dps[HVACMODE_DPS] = "wet"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)

        self.dps[HVACMODE_DPS] = "wind"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)

        self.dps[HVACMODE_DPS] = "auto"
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.OFF,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.COOL,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
            ],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "hot"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = 1
        self.assertEqual(self.subject.fan_mode, "auto")
        self.dps[FAN_DPS] = 2
        self.assertEqual(self.subject.fan_mode, "Turbo")
        self.dps[FAN_DPS] = 3
        self.assertEqual(self.subject.fan_mode, "low")
        self.dps[FAN_DPS] = 4
        self.assertEqual(self.subject.fan_mode, "medium")
        self.dps[FAN_DPS] = 5
        self.assertEqual(self.subject.fan_mode, "high")

    def test_fan_mode_invalid_in_dry_hvac_mode(self):
        self.dps[HVACMODE_DPS] = "wet"
        self.dps[FAN_DPS] = 1
        self.assertIs(self.subject.fan_mode, None)

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            [
                "auto",
                "Turbo",
                "low",
                "medium",
                "high",
            ],
        )

    async def test_set_fan_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 1},
        ):
            await self.subject.async_set_fan_mode("auto")

    async def test_set_fan_mode_to_turbo(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 2},
        ):
            await self.subject.async_set_fan_mode("Turbo")

    async def test_set_fan_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 3},
        ):
            await self.subject.async_set_fan_mode("low")

    async def test_set_fan_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 4},
        ):
            await self.subject.async_set_fan_mode("medium")

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: 5},
        ):
            await self.subject.async_set_fan_mode("high")

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            ["off", "horizontal", "vertical", "both"],
        )

    def test_swing_mode(self):
        self.dps[VSWING_DPS] = False
        self.dps[HSWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, "off")

        self.dps[VSWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, "vertical")

        self.dps[HSWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, "both")

        self.dps[VSWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, "horizontal")

    async def test_set_swing_mode_to_both(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HSWING_DPS: True, VSWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode("both")

    async def test_set_swing_mode_to_horizontal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HSWING_DPS: True, VSWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode("horizontal")

    async def test_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HSWING_DPS: False, VSWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode("off")

    async def test_set_swing_mode_to_vertical(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HSWING_DPS: False, VSWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode("vertical")

    def test_extra_state_attribures(self):
        self.dps[UNKNOWN8_DPS] = True
        self.dps[UNKNOWN12_DPS] = False
        self.dps[UNKNOWN102_DPS] = True
        self.dps[UNKNOWN103_DPS] = False
        self.dps[UNKNOWN108_DPS] = 108
        self.dps[UNKNOWN109_DPS] = 109
        self.dps[UNKNOWN110_DPS] = 110
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_8": True,
                "unknown_12": False,
                "unknown_102": True,
                "unknown_103": False,
                "unknown_108": 108,
                "unknown_109": 109,
                "unknown_110": 110,
            },
        )

    def test_light_icon(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")

    def test_switch_icon(self):
        self.assertEqual(self.basicSwitch.icon, "mdi:power-sleep")
