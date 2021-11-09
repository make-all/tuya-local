# Mixins for testing lights
from homeassistant.components.light import COLOR_MODE_ONOFF

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
        self.assertEqual(self.basicLight.device_state_attributes, {})
