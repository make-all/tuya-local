# Mixins for testing lights
from homeassistant.components.light import ColorMode

from ..helpers import assert_device_properties_set


class BasicLightTests:
    def setUpBasicLight(self, dps, subject, testdata=(True, False)):
        self.basicLight = subject
        self.basicLightDps = dps
        self.basicLightOn = testdata[0]
        self.basicLightOff = testdata[1]

    def test_basic_light_supported_features(self):
        self.assertEqual(self.basicLight.supported_features, 0)

    def test_basic_light_supported_color_modes(self):
        self.assertCountEqual(
            self.basicLight.supported_color_modes,
            [ColorMode.ONOFF],
        )

    def test_basic_light_color_mode(self):
        self.assertEqual(self.basicLight.color_mode, ColorMode.ONOFF)

    def test_basic_light_has_no_brightness(self):
        self.assertIsNone(self.basicLight.brightness)

    def test_basic_light_has_no_effects(self):
        self.assertIsNone(self.basicLight.effect_list)
        self.assertIsNone(self.basicLight.effect)

    def test_basic_light_is_on(self):
        self.dps[self.basicLightDps] = self.basicLightOn
        self.assertTrue(self.basicLight.is_on)
        self.dps[self.basicLightDps] = self.basicLightOff
        self.assertFalse(self.basicLight.is_on)

    async def test_basic_light_turn_on(self):
        self.dps[self.basicLightDps] = self.basicLightOff
        async with assert_device_properties_set(
            self.basicLight._device, {self.basicLightDps: self.basicLightOn}
        ):
            await self.basicLight.async_turn_on()

    async def test_basic_light_turn_off(self):
        self.dps[self.basicLightDps] = self.basicLightOn
        async with assert_device_properties_set(
            self.basicLight._device, {self.basicLightDps: self.basicLightOff}
        ):
            await self.basicLight.async_turn_off()

    async def test_basic_light_toggle_turns_on_when_it_was_off(self):
        self.dps[self.basicLightDps] = self.basicLightOff
        async with assert_device_properties_set(
            self.basicLight._device,
            {self.basicLightDps: self.basicLightOn},
        ):
            await self.basicLight.async_toggle()

    async def test_basic_light_toggle_turns_off_when_it_was_on(self):
        self.dps[self.basicLightDps] = self.basicLightOn
        async with assert_device_properties_set(
            self.basicLight._device,
            {self.basicLightDps: self.basicLightOff},
        ):
            await self.basicLight.async_toggle()

    def test_basic_light_state_attributes(self):
        self.assertEqual(self.basicLight.extra_state_attributes, {})


class MultiLightTests:
    def setUpMultiLights(self, lights):
        self.multiLight = {}
        self.multiLightDps = {}
        self.multiLightOn = {}
        self.multiLightOff = {}
        for l in lights:
            name = l["name"]
            subject = self.entities.get(name)
            testdata = l.get("testdata", (True, False))
            if subject is None:
                raise AttributeError(f"No light for {name} found.")
            self.multiLight[name] = subject
            self.multiLightDps[name] = l.get("dps")
            self.multiLightOn[name] = testdata[0]
            self.multiLightOff[name] = testdata[1]

    def test_multi_light_supported_features(self):
        for light in self.multiLight.values():
            self.assertEqual(light.supported_features, 0)

    def test_multi_light_supported_color_modes(self):
        for light in self.multiLight.values():
            self.assertCountEqual(
                light.supported_color_modes,
                [ColorMode.ONOFF],
            )

    def test_multi_light_color_mode(self):
        for light in self.multiLight.values():
            self.assertEqual(light.color_mode, ColorMode.ONOFF)

    def test_multi_lights_have_no_brightness(self):
        for light in self.multiLight.values():
            self.assertIsNone(light.brightness)

    def test_multi_lights_have_no_effects(self):
        for light in self.multiLight.values():
            self.assertIsNone(light.effect_list)
            self.assertIsNone(light.effect)

    def test_multi_light_is_on(self):
        for key, light in self.multiLight.items():
            dp_id = self.multiLightDps[key]
            self.dps[dp_id] = self.multiLightOn[key]
            self.assertTrue(light.is_on, f"{key} fails when ON")
            self.dps[dp_id] = self.multiLightOff[key]
            self.assertFalse(light.is_on, f"{key} fails when OFF")

    async def test_multi_light_turn_on(self):
        for key, light in self.multiLight.items():
            self.dps[self.multiLightDps[key]] = self.multiLightOff[key]
            async with assert_device_properties_set(
                light._device,
                {self.multiLightDps[key]: self.multiLightOn[key]},
                f"{key} failed to turn on",
            ):
                await light.async_turn_on()

    async def test_multi_light_turn_off(self):
        for key, light in self.multiLight.items():
            async with assert_device_properties_set(
                light._device,
                {self.multiLightDps[key]: self.multiLightOff[key]},
                f"{key} failed to turn off",
            ):
                await light.async_turn_off()

    async def test_multi_light_toggle_turns_on_when_it_was_off(self):
        for key, light in self.multiLight.items():
            self.dps[self.multiLightDps[key]] = self.multiLightOff[key]
            async with assert_device_properties_set(
                light._device,
                {self.multiLightDps[key]: self.multiLightOn[key]},
                f"{key} failed to toggle",
            ):
                await light.async_toggle()

    async def test_multi_light_toggle_turns_off_when_it_was_on(self):
        for key, light in self.multiLight.items():
            self.dps[self.multiLightDps[key]] = self.multiLightOn[key]
            async with assert_device_properties_set(
                light._device,
                {self.multiLightDps[key]: self.multiLightOff[key]},
                f"{key} failed to toggle",
            ):
                await light.async_toggle()

    def test_multi_light_state_attributes(self):
        for key, light in self.multiLight.items():
            self.assertEqual(
                light.extra_state_attributes,
                {},
                f"{key} extra_state_attributes mismatch",
            )


class DimmableLightTests:
    def setUpDimmableLight(
        self,
        dps,
        subject,
        offval=0,
        tests=[(100, 100)],
        no_off=False,
    ):
        self.dimmableLight = subject
        self.dimmableLightDps = dps
        self.dimmableLightOff = offval
        self.dimmableLightTest = tests
        self.dimmableLightNoOff = no_off

    def test_dimmable_light_brightness(self):
        self.dps[self.dimmableLightDps] = self.dimmableLightOff
        if not self.dimmableLightNoOff:
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
