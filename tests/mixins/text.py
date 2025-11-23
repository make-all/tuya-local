# Mixins for testing text entities
from homeassistant.components.text import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_PATTERN,
    TextMode,
)

from ..helpers import assert_device_properties_set

TEXT_PATTERN_HEX = "[0-9a-fA-F]*"
TEXT_PATTERN_BASE64 = "[-A-Za-z0-9+/]*={0,3}"


class BasicTextTests:
    def setUpBasicText(
        self,
        dp,
        subject,
        max=None,
        min=None,
        mode=TextMode.TEXT,
        pattern=None,
        testdata=None,
        extra_state={},
    ):
        self.basicText = subject
        self.basicTextDp = dp
        self.basicTextMin = min
        self.basicTextMax = max
        self.basicTextMode = mode
        self.basicTextPattern = pattern
        self.basicTextTestData = testdata
        self.basicTextExtra = extra_state

    def test_text_min_value(self):
        if self.basicTextMin is not None:
            self.assertEqual(self.basicText._attr_native_min, self.basicTextMin)

    def test_text_max_value(self):
        if self.basicTextMax is not None:
            self.assertEqual(self.basicText._attr_native_max, self.basicTextMax)

    def test_text_mode(self):
        if self.basicTextMode is not None:
            self.assertEqual(self.basicText._attr_mode, self.basicTextMode)

    def test_text_pattern(self):
        if self.basicTextPattern is not None:
            self.assertEqual(self.basicText._attr_pattern, self.basicTextPattern)

    def test_text_value(self):
        if self.basicTextTestData:
            val = self.basicTextTestData[0]
            expected = self.basicTextTestData[1]
        else:
            val = "ipsum"
            expected = "ipsum"
        self.dps[self.basicTextDp] = val
        self.assertEqual(self.basicText.native_value, expected)

    async def test_text_set_value(self):
        if self.basicTextTestData:
            dps_val = self.basicTextTestData[0]
            val = self.basicTextTestData[1]
        else:
            dps_val = "ipsum"
            val = "ipsum"
        async with assert_device_properties_set(
            self.basicText._device, {self.basicTextDp: dps_val}
        ):
            await self.basicText.async_set_value(val)

    def test_text_extra_state_attributes(self):
        expected = {ATTR_MODE: self.basicTextMode, **self.basicTextExtra}
        if self.basicTextPattern:
            expected[ATTR_PATTERN] = self.basicTextPattern
        if self.basicTextMin:
            expected[ATTR_MIN] = self.basicTextMin
        if self.basicTextMax:
            expected[ATTR_MAX] = self.basicTextMax
        self.assertEqual(self.basicText.extra_state_attributes, expected)


class MultiTextTests:
    def setUpMultiText(self, texts):
        self.multiText = {}
        self.multiTextDps = {}
        self.multiTextMin = {}
        self.multiTextMax = {}
        self.multiTextMode = {}
        self.multiTextPattern = {}
        self.multiTextTestData = {}
        self.multiTextExtra = {}
        for text in texts:
            name = text.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No text for {name} found.")
            self.multiText[name] = subject
            self.multiTextDps[name] = text.get("dps")
            self.multiTextMin[name] = text.get("min", 0)
            self.multiTextMax[name] = text.get("max")
            self.multiTextMode[name] = text.get("mode", TextMode.TEXT)
            self.multiTextPattern[name] = text.get("pattern")
            self.multiTextTestData[name] = text.get("testdata")
            self.multiTextExtra[name] = text.get("extra", {})

    def test_multi_text_min_value(self):
        for key, subject in self.multiText.items():
            if self.multiTextMin.get(key):
                self.assertEqual(
                    subject.native_min_value,
                    self.multiTextMin[key],
                    f"{key} min value mismatch",
                )

    def test_multi_text_max_value(self):
        for key, subject in self.multiText.items():
            if self.multiTextMax.get(key):
                self.assertEqual(
                    subject.native_max_value,
                    self.multiTextMax[key],
                    f"{key} max value mismatch",
                )

    def test_multi_text_mode(self):
        for key, subject in self.multiText.items():
            if self.multiTextMode.get(key):
                self.assertEqual(subject.mode, self.multiTextMode[key])

    def test_multi_text_pattern(self):
        for key, subject in self.multiText.items():
            if self.multiTextPattern.get(key):
                self.assertEqual(subject.pattern, self.multiTextPattern[key])

    def test_multi_text_value(self):
        for key, subject in self.multiText.items():
            if self.multiTextTestData.get(key):
                val = self.multiTextTestData[key][0]
                expected = self.multiTextTestData[key][1]
            else:
                val = "ipsum"
                expected = "ipsum"
            self.dps[self.multiTextDp[key]] = val
            self.assertEqual(subject.native_value, expected)

    async def test_multi_text_set_value(self):
        for key, subject in self.multiText.items():
            await subject.async_set_value("lorem")
            self.assert_device_properties_set(self.multiTextDp[key], "lorem")

    def test_multi_text_extra_state_attributes(self):
        for key, subject in self.multiText.items():
            expected = {
                ATTR_MODE: self.multiTextMode[key],
                **self.multiTextExtra[key],
            }
            if self.multiTextPattern.get(key):
                expected[ATTR_PATTERN] = self.multiTextPattern[key]
            if self.multiTextMin.get(key):
                expected[ATTR_MIN] = self.multiTextMin[key]
            if self.multiTextMax.get(key):
                expected[ATTR_MAX] = self.multiTextMax[key]
            self.assertEqual(subject.extra_state_attributes, expected)
