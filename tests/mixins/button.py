# Mixins for testing buttons
from homeassistant.components.button import ButtonDeviceClass

from ..helpers import assert_device_properties_set


class BasicButtonTests:
    def setUpBasicButton(
        self,
        dps,
        subject,
        device_class=None,
        testdata=True,
    ):
        self.basicButton = subject
        self.basicButtonDps = dps
        try:
            self.basicButtonDevClass = ButtonDeviceClass(device_class)
        except ValueError:
            self.basicButtonDevClass = None

        self.basicButtonPushData = testdata

    async def test_basic_button_press(self):
        async with assert_device_properties_set(
            self.basicButton._device,
            {self.basicButtonDps: self.basicButtonPushData},
        ):
            await self.basicButton.async_press()

    def test_basic_button_device_class(self):
        self.assertEqual(self.basicButton.device_class, self.basicButtonDevClass)

    def test_basic_button_extra_attributes(self):
        self.assertEqual(self.basicButton.extra_state_attributes, {})


class MultiButtonTests:
    def setUpMultiButtons(self, buttons):
        self.multiButton = {}
        self.multiButtonDps = {}
        self.multiButtonDevClass = {}
        self.multiButtonPushData = {}

        for b in buttons:
            name = b.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No button for {name} found.")
            self.multiButton[name] = subject
            self.multiButtonDps[name] = b.get("dps")
            self.multiButtonPushData[name] = b.get("testdata", True)
            try:
                self.multiButtonDevClass[name] = ButtonDeviceClass(
                    b.get("device_class", None)
                )
            except ValueError:
                self.multiButtonDevClass[name] = None

    async def test_multi_button_press(self):
        for key, subject in self.multiButton.items():
            dp = self.multiButtonDps[key]
            async with assert_device_properties_set(
                subject._device,
                {dp: self.multiButtonPushData[key]},
            ):
                await subject.async_press()

    def test_multi_button_device_class(self):
        for key, subject in self.multiButton.items():
            self.assertEqual(subject.device_class, self.multiButtonDevClass[key])

    def test_multi_button_extra_attributes(self):
        for subject in self.multiButton.values():
            self.assertEqual(subject.extra_state_attributes, {})
