# Mixins for testing select entities
from ..helpers import assert_device_properties_set


class BasicSelectTests:
    def setUpBasicSelect(self, dps, subject, options):
        self.basicSelect = subject
        self.basicSelectDps = dps
        self.basicSelectOptions = options

    def test_basicSelect_options(self):
        self.assertCountEqual(
            self.basicSelect.options,
            self.basicSelectOptions.values(),
        )

    def test_basicSelect_current_option(self):
        for dpsVal, val in self.basicSelectOptions.items():
            self.dps[self.basicSelectDps] = dpsVal
            self.assertEqual(self.basicSelect.current_option, val)

    async def test_basicSelect_select_option(self):
        for dpsVal, val in self.basicSelectOptions.items():
            async with assert_device_properties_set(
                self.basicSelect._device, {self.basicSelectDps: dpsVal}
            ):
                await self.basicSelect.async_select_option(val)

    def test_basicSelect_extra_state_attributes(self):
        self.assertEqual(self.basicSelect.extra_state_attributes, {})


class MultiSelectTests:
    def setUpMultiSelect(self, selects):
        self.multiSelect = {}
        self.multiSelectDps = {}
        self.multiSelectOptions = {}
        for s in selects:
            name = s.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No select for {name} found.")
            self.multiSelect[name] = subject
            self.multiSelectDps[name] = s.get("dps")
            self.multiSelectOptions[name] = s.get("options")

    def test_multiSelect_options(self):
        for key, subject in self.multiSelect.items():
            with self.subTest(key):
                self.assertCountEqual(
                    subject.options,
                    self.multiSelectOptions[key].values(),
                )

    def test_multiSelect_current_option(self):
        for key, subject in self.multiSelect.items():
            with self.subTest(key):
                for dpsVal, val in self.multiSelectOptions[key].items():
                    self.dps[self.multiSelectDps[key]] = dpsVal
                    self.assertEqual(subject.current_option, val)

    async def test_multiSelect_select_option(self):
        for key, subject in self.multiSelect.items():
            with self.subTest(key):
                for dpsVal, val in self.multiSelectOptions[key].items():
                    async with assert_device_properties_set(
                        subject._device, {self.multiSelectDps[key]: dpsVal}
                    ):
                        await subject.async_select_option(val)

    def test_multiSelect_extra_state_attributes(self):
        for key, subject in self.multiSelect.items():
            with self.subTest(key):
                self.assertEqual(subject.extra_state_attributes, {})
