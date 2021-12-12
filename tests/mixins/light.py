# Mixins for testing lights
from homeassistant.components.light import (
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
)

from ..helpers import assert_device_properties_set


class BasicLightTests:
    def setUpBasicLight(self, dps, subject):
        self.basicLight = subject
        self.basicLightDps = dps

    def test_basic_light_supported_features(self):
        self.assertEqual(self.basicLight.supported_features, 0)

    def test_basic_light_supported_color_modes(self):
        self.assertCountEqual(
            self.basicLight.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_basic_light_color_mode(self):
        self.assertEqual(self.basicLight.color_mode, COLOR_MODE_ONOFF)

    def test_light_has_no_brightness(self):
        self.assertIsNone(self.basicLight.brightness)

    def test_light_has_no_effects(self):
        self.assertIsNone(self.basicLight.effect_list)
        self.assertIsNone(self.basicLight.effect)

    def test_basic_light_is_on(self):
        self.dps[self.basicLightDps] = True
        self.assertTrue(self.basicLight.is_on)
        self.dps[self.basicLightDps] = False
        self.assertFalse(self.basicLight.is_on)

    async def test_basic_light_turn_on(self):
        async with assert_device_properties_set(
            self.basicLight._device, {self.basicLightDps: True}
        ):
            await self.basicLight.async_turn_on()

    async def test_basic_light_turn_off(self):
        async with assert_device_properties_set(
            self.basicLight._device, {self.basicLightDps: False}
        ):
            await self.basicLight.async_turn_off()

    async def test_basic_light_toggle_turns_on_when_it_was_off(self):
        self.dps[self.basicLightDps] = False
        async with assert_device_properties_set(
            self.basicLight._device,
            {self.basicLightDps: True},
        ):
            await self.basicLight.async_toggle()

    async def test_basic_light_toggle_turns_off_when_it_was_on(self):
        self.dps[self.basicLightDps] = True
        async with assert_device_properties_set(
            self.basicLight._device,
            {self.basicLightDps: False},
        ):
            await self.basicLight.async_toggle()

    def test_basic_light_state_attributes(self):
        self.assertEqual(self.basicLight.extra_state_attributes, {})


class DimmableLightTests:
    def setUpDimmableLight(self, dps, subject, offval=0, tests=[(100, 100)]):
        self.dimmableLight = subject
        self.dimmableLightDps = dps
        self.dimmableLightOff = offval
        self.dimmableLightTest = tests

    def test_dimmable_light_supported_features(self):
        self.dps[self.dimmableLightDps] = self.dimmableLightOff
        self.assertFalse(self.dimmableLight.is_on)
        self.dps[self.dimmableLightDps] = self.dimmableLightTest[0][0]
        self.assertTrue(self.dimmableLight.is_on)
        self.dps[self.dimmableLightDps] = None
        self.assertFalse(self.dimmableLight.is_on)

    def test_dimmable_light_brightness(self):
        self.dps[self.dimmableLightDps] = self.dimmableLightOff
        self.assertEqual(self.dimmableLight.brightness, 0)
        for dps, val in self.dimmableLightTest:
            self.dps[self.dimmableLightDps] = dps
            self.assertEqual(self.dimmableLight.brightness, val)

    def test_dimmable_light_state_attributes(self):
        self.assertEqual(self.dimmableLight.extra_state_attributes, {})

    async def test_dimmable_light_turn_off(self):
        async with assert_device_properties_set(
            self.dimmableLight._device,
            {self.dimmableLightDps: self.dimmableLightOff},
        ):
            await self.dimmableLight.async_turn_off()

    async def test_dimmable_light_set_brightness(self):
        for dps, val in self.dimmableLightTest:
            async with assert_device_properties_set(
                self.dimmableLight._device,
                {self.dimmableLightDps: dps},
            ):
                await self.dimmableLight.async_turn_on(brightness=val)

    async def test_dimmable_light_set_brightness_to_off(self):
        async with assert_device_properties_set(
            self.dimmableLight._device,
            {self.dimmableLightDps: self.dimmableLightOff},
        ):
            await self.dimmableLight.async_turn_on(brightness=0)

    async def test_dimmable_light_toggle_turns_off_when_it_was_on(self):
        self.dps[self.dimmableLightDps] = self.dimmableLightTest[0][0]
        async with assert_device_properties_set(
            self.dimmableLight._device,
            {self.dimmableLightDps: self.dimmableLightOff},
        ):
            await self.dimmableLight.async_toggle()
