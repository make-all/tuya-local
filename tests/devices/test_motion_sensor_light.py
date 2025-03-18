from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.const import LIGHT_LUX, UnitOfTime

from ..const import MOTION_LIGHT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.number import MultiNumberTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

EFFECT_DPS = "101"
SWITCH_DPS = "102"
PROX_DPS = "103"
TIME_DPS = "104"
LUX_DPS = "105"
RESET_DPS = "106"


class TestMotionLight(BasicSwitchTests, MultiNumberTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("motion_sensor_light.yaml", MOTION_LIGHT_PAYLOAD)
        self.subject = self.entities.get("light")
        self.auto_sw = self.entities.get("switch_auto_mode")
        self.setUpBasicSwitch(RESET_DPS, self.entities.get("switch_auto_reset"))
        self.setUpMultiNumber(
            [
                {
                    "dps": PROX_DPS,
                    "name": "number_sensitivity",
                    "min": 0,
                    "max": 4,
                    "testdata": (1, 3),
                },
                {
                    "dps": TIME_DPS,
                    "name": "number_duration",
                    "device_class": NumberDeviceClass.DURATION,
                    "min": 10,
                    "max": 900,
                    "step": 10,
                    "unit": UnitOfTime.SECONDS,
                },
                {
                    "dps": LUX_DPS,
                    "name": "number_light_level",
                    "device_class": NumberDeviceClass.ILLUMINANCE,
                    "min": 0,
                    "max": 3900,
                    "unit": LIGHT_LUX,
                    "testdata": (1900, 2000),
                },
            ]
        )
        self.mark_secondary(
            [
                "number_duration",
                "number_light_level",
                "number_sensitivity",
                "switch_auto_reset",
            ]
        )

    def test_effects(self):
        self.assertCountEqual(
            self.subject.effect_list,
            ["auto", "off", "on"],
        )

    def test_effect(self):
        self.dps[EFFECT_DPS] = "mode_on"
        self.assertEqual(self.subject.effect, "on")
        self.dps[EFFECT_DPS] = "mode_off"
        self.assertEqual(self.subject.effect, "off")
        self.dps[EFFECT_DPS] = "mode_auto"
        self.assertEqual(self.subject.effect, "auto")

    def test_is_on_reflects_switch(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    async def test_turn_on_via_effect(self):
        self.dps[SWITCH_DPS] = False
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_on"},
        ):
            await self.subject.async_turn_on()

    async def test_turn_off_via_effect(self):
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_off"},
        ):
            await self.subject.async_turn_off()

    async def test_set_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_auto"},
        ):
            await self.subject.async_turn_on(effect="auto")

    def test_auto_mode_is_on(self):
        self.dps[SWITCH_DPS] = False
        self.dps[EFFECT_DPS] = "mode_auto"
        self.assertTrue(self.auto_sw.is_on)
        self.assertFalse(self.subject.is_on)
        self.dps[EFFECT_DPS] = "mode_off"
        self.assertFalse(self.auto_sw.is_on)
        self.assertFalse(self.subject.is_on)
        self.dps[SWITCH_DPS] = True
        self.dps[EFFECT_DPS] = "mode_auto"
        self.assertTrue(self.auto_sw.is_on)
        self.assertTrue(self.subject.is_on)
        self.dps[EFFECT_DPS] = "mode_on"
        self.assertFalse(self.auto_sw.is_on)
        self.assertTrue(self.subject.is_on)

    async def test_auto_mode_async_turn_on_off(self):
        self.dps[SWITCH_DPS] = True
        self.dps[EFFECT_DPS] = "mode_auto"
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_on"},
        ):
            await self.auto_sw.async_turn_off()

        self.dps[SWITCH_DPS] = False
        self.dps[EFFECT_DPS] = "mode_auto"
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_off"},
        ):
            await self.auto_sw.async_turn_off()

        self.dps[SWITCH_DPS] = True
        self.dps[EFFECT_DPS] = "mode_on"
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_auto"},
        ):
            await self.auto_sw.async_turn_on()

        self.dps[SWITCH_DPS] = False
        self.dps[EFFECT_DPS] = "mode_off"
        async with assert_device_properties_set(
            self.subject._device,
            {EFFECT_DPS: "mode_auto"},
        ):
            await self.auto_sw.async_turn_on()
