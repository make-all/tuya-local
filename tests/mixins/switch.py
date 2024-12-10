# Mixins for testing switches
from homeassistant.components.switch import SwitchDeviceClass

from ..helpers import assert_device_properties_set


class SwitchableTests:
    def setUpSwitchable(self, dps, subject):
        self.switch_dps = dps
        self.switch_subject = subject

    def test_switchable_is_on(self):
        self.dps[self.switch_dps] = True
        self.assertTrue(self.switch_subject.is_on)

        self.dps[self.switch_dps] = False
        self.assertFalse(self.switch_subject.is_on)

        self.dps[self.switch_dps] = None
        self.assertIsNone(self.switch_subject.is_on)

    async def test_switchable_turn_on(self):
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: True}
        ):
            await self.switch_subject.async_turn_on()

    async def test_switchable_turn_off(self):
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: False}
        ):
            await self.switch_subject.async_turn_off()

    async def test_switchable_toggle(self):
        self.dps[self.switch_dps] = False
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: True}
        ):
            await self.switch_subject.async_toggle()

        self.dps[self.switch_dps] = True
        async with assert_device_properties_set(
            self.switch_subject._device, {self.switch_dps: False}
        ):
            await self.switch_subject.async_toggle()


class BasicSwitchTests:
    def setUpBasicSwitch(
        self,
        dps,
        subject,
        device_class=None,
        power_dps=None,
        power_scale=1,
        testdata=(True, False),
    ):
        self.basicSwitch = subject
        self.basicSwitchDps = dps
        try:
            self.basicSwitchDevClass = SwitchDeviceClass(device_class)
        except ValueError:
            self.basicSwitchDevClass = None

        self.basicSwitchPowerDps = power_dps
        self.basicSwitchPowerScale = power_scale
        self.basicSwitchOn = testdata[0]
        self.basicSwitchOff = testdata[1]

    def test_basic_switch_is_on(self):
        self.dps[self.basicSwitchDps] = self.basicSwitchOn
        self.assertEqual(self.basicSwitch.is_on, True)

        self.dps[self.basicSwitchDps] = self.basicSwitchOff
        self.assertEqual(self.basicSwitch.is_on, False)

    async def test_basic_switch_turn_on(self):
        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: self.basicSwitchOn}
        ):
            await self.basicSwitch.async_turn_on()

    async def test_basic_switch_turn_off(self):
        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: self.basicSwitchOff}
        ):
            await self.basicSwitch.async_turn_off()

    async def test_basic_switch_toggle_turns_on_when_it_was_off(self):
        self.dps[self.basicSwitchDps] = self.basicSwitchOff

        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: self.basicSwitchOn}
        ):
            await self.basicSwitch.async_toggle()

    async def test_basic_switch_toggle_turns_off_when_it_was_on(self):
        self.dps[self.basicSwitchDps] = self.basicSwitchOn

        async with assert_device_properties_set(
            self.basicSwitch._device, {self.basicSwitchDps: self.basicSwitchOff}
        ):
            await self.basicSwitch.async_toggle()

    def test_basic_switch_class_device_class(self):
        self.assertEqual(self.basicSwitch.device_class, self.basicSwitchDevClass)

    def test_basic_switch_state_attributes(self):
        self.assertEqual(self.basicSwitch.extra_state_attributes, {})


class MultiSwitchTests:
    def setUpMultiSwitch(self, switches):
        self.multiSwitch = {}
        self.multiSwitchDps = {}
        self.multiSwitchDevClass = {}
        self.multiSwitchPowerDps = {}
        self.multiSwitchPowerScale = {}

        for s in switches:
            name = s.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No switch for {name} found.")
            self.multiSwitch[name] = subject
            self.multiSwitchDps[name] = s.get("dps")
            try:
                self.multiSwitchDevClass[name] = SwitchDeviceClass(
                    s.get("device_class")
                )
            except ValueError:
                self.multiSwitchDevClass[name] = None

            self.multiSwitchPowerDps[name] = s.get("power_dps")
            self.multiSwitchPowerScale[name] = s.get("power_scale", 1)

    def test_multi_switch_is_on(self):
        for key, subject in self.multiSwitch.items():
            dp = self.multiSwitchDps[key]
            self.dps[dp] = True
            self.assertEqual(subject.is_on, True, f"{key} fails when ON")

            self.dps[dp] = False
            self.assertEqual(subject.is_on, False, f"{key} fails when OFF")

    async def test_multi_switch_turn_on(self):
        for key, subject in self.multiSwitch.items():
            async with assert_device_properties_set(
                subject._device,
                {self.multiSwitchDps[key]: True},
                f"{key} failed to turn on",
            ):
                await subject.async_turn_on()

    async def test_multi_switch_turn_off(self):
        for key, subject in self.multiSwitch.items():
            async with assert_device_properties_set(
                subject._device,
                {self.multiSwitchDps[key]: False},
                f"{key} failed to turn off",
            ):
                await subject.async_turn_off()

    async def test_multi_switch_toggle_turns_on_when_it_was_off(self):
        for key, subject in self.multiSwitch.items():
            dp = self.multiSwitchDps[key]
            self.dps[dp] = False

            async with assert_device_properties_set(
                subject._device, {dp: True}, f"{key} failed to toggle"
            ):
                await subject.async_toggle()

    async def test_multi_switch_toggle_turns_off_when_it_was_on(self):
        for key, subject in self.multiSwitch.items():
            dp = self.multiSwitchDps[key]
            self.dps[dp] = True

            async with assert_device_properties_set(
                subject._device, {dp: False}, f"{key} failed to toggle"
            ):
                await subject.async_toggle()

    def test_multi_switch_device_class(self):
        for key, subject in self.multiSwitch.items():
            self.assertEqual(
                subject.device_class,
                self.multiSwitchDevClass[key],
                f"{key} device_class mismatch",
            )

    def test_multi_switch_state_attributes(self):
        for key, subject in self.multiSwitch.items():
            self.assertEqual(
                subject.extra_state_attributes,
                {},
                f"{key} has unexpected extra_state_attributes",
            )
