# Mixins for testing number entities
from ..helpers import assert_device_properties_set


class BasicNumberTests:
    def setUpBasicNumber(
        self, dps, subject, max, min=0, step=1, mode="auto", scale=1, unit=None
    ):
        self.basicNumber = subject
        self.basicNumberDps = dps
        self.basicNumberMin = min
        self.basicNumberMax = max
        self.basicNumberStep = step
        self.basicNumberMode = mode
        self.basicNumberScale = scale
        self.basicNumberUnit = unit

    def test_number_min_value(self):
        self.assertEqual(self.basicNumber.min_value, self.basicNumberMin)

    def test_number_max_value(self):
        self.assertEqual(self.basicNumber.max_value, self.basicNumberMax)

    def test_number_step(self):
        self.assertEqual(self.basicNumber.step, self.basicNumberStep)

    def test_number_mode(self):
        self.assertEqual(self.basicNumber.mode, self.basicNumberMode)

    def test_number_unit_of_measurement(self):
        self.assertEqual(self.basicNumber.unit_of_measurement, self.basicNumberUnit)

    def test_number_value(self):
        val = min(max(self.basicNumberMin, self.basicNumberStep), self.basicNumberMax)
        dps_val = val * self.basicNumberScale
        self.dps[self.basicNumberDps] = dps_val
        self.assertEqual(self.basicNumber.value, val)

    async def test_number_set_value(self):
        val = min(max(self.basicNumberMin, self.basicNumberStep), self.basicNumberMax)
        dps_val = val * self.basicNumberScale
        async with assert_device_properties_set(
            self.basicNumber._device, {self.basicNumberDps: dps_val}
        ):
            await self.basicNumber.async_set_value(val)

    def test_number_extra_state_attributes(self):
        self.assertEqual(self.basicNumber.extra_state_attributes, {})


class MultiNumberTests:
    def setUpMultiNumber(self, numbers):
        self.multiNumber = {}
        self.multiNumberDps = {}
        self.multiNumberMin = {}
        self.multiNumberMax = {}
        self.multiNumberStep = {}
        self.multiNumberMode = {}
        self.multiNumberScale = {}
        self.multiNumberUnit = {}

        for n in numbers:
            name = n.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No number for {name} found.")
            self.multiNumber[name] = subject
            self.multiNumberDps[name] = n.get("dps")
            self.multiNumberMin[name] = n.get("min", 0)
            self.multiNumberMax[name] = n.get("max")
            self.multiNumberStep[name] = n.get("step", 1)
            self.multiNumberMode[name] = n.get("mode", "auto")
            self.multiNumberScale[name] = n.get("scale", 1)
            self.multiNumberUnit[name] = n.get("unit", None)

    def test_multi_number_min_value(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                self.assertEqual(subject.min_value, self.multiNumberMin[key])

    def test_multi_number_max_value(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                self.assertEqual(subject.max_value, self.multiNumberMax[key])

    def test_multi_number_step(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                self.assertEqual(subject.step, self.multiNumberStep[key])

    def test_multi_number_mode(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                self.assertEqual(subject.mode, self.multiNumberMode[key])

    def test_multi_number_unit_of_measurement(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                self.assertEqual(subject.unit_of_measurement, self.multiNumberUnit[key])

    def test_multi_number_value(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                val = min(
                    max(self.multiNumberMin[key], self.multiNumberStep[key]),
                    self.multiNumberMax[key],
                )
                dps_val = val * self.multiNumberScale[key]
                self.dps[self.multiNumberDps[key]] = dps_val
                self.assertEqual(subject.value, val)

    async def test_multi_number_set_value(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                val = min(
                    max(self.multiNumberMin[key], self.multiNumberStep[key]),
                    self.multiNumberMax[key],
                )
                dps_val = val * self.multiNumberScale[key]
                async with assert_device_properties_set(
                    subject._device, {self.multiNumberDps[key]: dps_val}
                ):
                    await subject.async_set_value(val)

    def test_multi_number_extra_state_attributes(self):
        for key, subject in self.multiNumber.items():
            with self.subTest(key):
                self.assertEqual(subject.extra_state_attributes, {})
