from homeassistant.components.climate.const import (
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_SLEEP,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE as SUPPORT_CLIMATE_PRESET,
    SUPPORT_SWING_MODE,
    SWING_HORIZONTAL,
    SWING_OFF,
)
from homeassistant.components.fan import (
    SUPPORT_OSCILLATE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
)

from homeassistant.const import STATE_UNAVAILABLE

from ..const import FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
FANMODE_DPS = "2"
PRESET_DPS = "3"
SWING_DPS = "8"
TIMER_DPS = "11"
LIGHT_DPS = "101"


class TestGoldairFan(BasicLightTests, SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("goldair_fan.yaml", FAN_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.climate = self.entities.get("climate")
        self.setUpSwitchable(HVACMODE_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.mark_secondary(["light_display"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_OSCILLATE | SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED,
        )
        self.assertEqual(
            self.climate.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_CLIMATE_PRESET | SUPPORT_SWING_MODE,
        )

    def test_climate_icon_is_fan(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.climate.icon, "mdi:fan")
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.climate.icon, "mdi:fan-off")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.climate.temperature_unit, self.climate._device.temperature_unit
        )

    def test_is_on(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.climate.hvac_mode, HVAC_MODE_FAN_ONLY)
        self.assertTrue(self.subject.is_on)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.climate.hvac_mode, HVAC_MODE_OFF)
        self.assertFalse(self.subject.is_on)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.climate.hvac_mode, STATE_UNAVAILABLE)
        self.assertIsNone(self.subject.is_on)

    def test_climate_hvac_modes(self):
        self.assertCountEqual(
            self.climate.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY]
        )

    async def test_climate_turn_on(self):
        async with assert_device_properties_set(
            self.climate._device, {HVACMODE_DPS: True}
        ):
            await self.climate.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    async def test_climate_turn_off(self):
        async with assert_device_properties_set(
            self.climate._device, {HVACMODE_DPS: False}
        ):
            await self.climate.async_set_hvac_mode(HVAC_MODE_OFF)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_turn_off()

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.climate.preset_mode, "normal")
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.climate.preset_mode, PRESET_ECO)
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = PRESET_SLEEP
        self.assertEqual(self.climate.preset_mode, PRESET_SLEEP)
        self.assertEqual(self.subject.preset_mode, PRESET_SLEEP)

        self.dps[PRESET_DPS] = None
        self.assertIs(self.climate.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.climate.preset_modes, ["normal", PRESET_ECO, PRESET_SLEEP]
        )
        self.assertCountEqual(self.subject.preset_modes, ["normal", "nature", "sleep"])

    async def test_set_climate_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.climate._device,
            {PRESET_DPS: "normal"},
        ):
            await self.climate.async_set_preset_mode("normal")

    async def test_set_climate_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.climate._device,
            {PRESET_DPS: "nature"},
        ):
            await self.climate.async_set_preset_mode(PRESET_ECO)

    async def test_set_climate_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.climate._device,
            {PRESET_DPS: PRESET_SLEEP},
        ):
            await self.climate.async_set_preset_mode(PRESET_SLEEP)

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_nature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "nature"},
        ):
            await self.subject.async_set_preset_mode("nature")

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.climate.swing_mode, SWING_OFF)
        self.assertFalse(self.subject.oscillating)

        self.dps[SWING_DPS] = True
        self.assertEqual(self.climate.swing_mode, SWING_HORIZONTAL)
        self.assertTrue(self.subject.oscillating)

        self.dps[SWING_DPS] = None
        self.assertIs(self.climate.swing_mode, None)
        self.assertFalse(self.subject.oscillating)

    def test_swing_modes(self):
        self.assertCountEqual(self.climate.swing_modes, [SWING_OFF, SWING_HORIZONTAL])

    async def test_climate_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.climate._device,
            {SWING_DPS: False},
        ):
            await self.climate.async_set_swing_mode(SWING_OFF)

    async def test_climate_set_swing_mode_to_horizontal(self):
        async with assert_device_properties_set(
            self.climate._device,
            {SWING_DPS: True},
        ):
            await self.climate.async_set_swing_mode(SWING_HORIZONTAL)

    async def test_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: False}
        ):
            await self.subject.async_oscillate(False)

    async def test_oscillate_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWING_DPS: True}
        ):
            await self.subject.async_oscillate(True)

    def test_speed(self):
        self.dps[PRESET_DPS] = "normal"
        self.dps[FANMODE_DPS] = 6
        self.assertEqual(self.subject.percentage, 50)

    async def test_set_speed_in_normal_mode(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 3}):
            await self.subject.async_set_percentage(25)

    async def test_set_speed_in_normal_mode_snaps(self):
        self.dps[PRESET_DPS] = "normal"
        async with assert_device_properties_set(
            self.subject._device, {FANMODE_DPS: 10}
        ):
            await self.subject.async_set_percentage(80)

    async def test_set_speed_in_sleep_mode_snaps(self):
        self.dps[PRESET_DPS] = "sleep"
        async with assert_device_properties_set(self.subject._device, {FANMODE_DPS: 8}):
            await self.subject.async_set_percentage(75)

    def test_climate_fan_modes(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertCountEqual(self.climate.fan_modes, list(range(1, 13)))

        self.dps[PRESET_DPS] = "nature"
        self.assertCountEqual(self.climate.fan_modes, ["low", "medium", "high"])

        self.dps[PRESET_DPS] = PRESET_SLEEP
        self.assertCountEqual(self.climate.fan_modes, ["low", "medium", "high"])

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.climate.fan_modes, None)

    def test_climate_fan_mode_for_normal_preset(self):
        self.dps[PRESET_DPS] = "normal"

        self.dps[FANMODE_DPS] = 1
        self.assertEqual(self.climate.fan_mode, 1)

        self.dps[FANMODE_DPS] = 6
        self.assertEqual(self.climate.fan_mode, 6)

        self.dps[FANMODE_DPS] = 12
        self.assertEqual(self.climate.fan_mode, 12)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    async def test_climate_set_fan_mode_for_normal_preset(self):
        self.dps[PRESET_DPS] = "normal"

        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: 6},
        ):
            await self.climate.async_set_fan_mode(6)

    def test_climate_fan_mode_for_eco_preset(self):
        self.dps[PRESET_DPS] = "nature"

        self.dps[FANMODE_DPS] = 4
        self.assertEqual(self.climate.fan_mode, "low")

        self.dps[FANMODE_DPS] = 8
        self.assertEqual(self.climate.fan_mode, "medium")

        self.dps[FANMODE_DPS] = 12
        self.assertEqual(self.climate.fan_mode, "high")

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    async def test_climate_set_fan_mode_for_eco_preset(self):
        self.dps[PRESET_DPS] = "nature"

        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: 4},
        ):
            await self.climate.async_set_fan_mode("low")

    def test_climate_fan_mode_for_sleep_preset(self):
        self.dps[PRESET_DPS] = PRESET_SLEEP

        self.dps[FANMODE_DPS] = 4
        self.assertEqual(self.climate.fan_mode, "low")

        self.dps[FANMODE_DPS] = 8
        self.assertEqual(self.climate.fan_mode, "medium")

        self.dps[FANMODE_DPS] = 12
        self.assertEqual(self.climate.fan_mode, "high")

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.climate.fan_mode, None)

    async def test_climate_set_fan_mode_for_sleep_preset(self):
        self.dps[PRESET_DPS] = PRESET_SLEEP

        async with assert_device_properties_set(
            self.climate._device,
            {FANMODE_DPS: 8},
        ):
            await self.climate.async_set_fan_mode("medium")

    def test_extra_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.assertEqual(self.climate.extra_state_attributes, {"timer": "5"})
        self.assertEqual(self.subject.extra_state_attributes, {"timer": "5"})

    def test_light_icon(self):
        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")

        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")
