# Mixins for testing number entities
from ..helpers import assert_device_properties_set


class BasicNumberTests:
    def setUpBasicNumber(
        self,
        dps,
        subject,
        max,
        min=0,
        step=1,
        mode="auto",
        scale=1,
        unit=None,
        testdata=None,
        device_class=None,
    ):
        self.basicNumber = subject
        self.basicNumberDps = dps
        self.basicNumberMin = min
        self.basicNumberMax = max
        self.basicNumberStep = step
        self.basicNumberMode = mode
        self.basicNumberScale = scale
        self.basicNumberUnit = unit
        self.basicNumberTestData = testdata
        self.basicNumberDevClass = device_class

    def test_number_min_value(self):
        self.assertEqual(self.basicNumber.native_min_value, self.basicNumberMin)

    def test_number_max_value(self):
        self.assertEqual(self.basicNumber.native_max_value, self.basicNumberMax)

    def test_number_step(self):
        self.assertEqual(self.basicNumber.native_step, self.basicNumberStep)

    def test_number_mode(self):
        self.assertEqual(self.basicNumber.mode, self.basicNumberMode)

    def test_number_unit_of_measurement(self):
        self.assertEqual(
            self.basicNumber.native_unit_of_measurement, self.basicNumberUnit
        )

    def test_number_device_class(self):
        self.assertEqual(
            self.basicNumber.device_class,
            self.basicNumberDevClass,
        )

    def test_number_value(self):
        if self.basicNumberTestData:
            val = self.basicNumberTestData[0]
            expected = self.basicNumberTestData[1]
        else:
            expected = min(
                max(self.basicNumberMin, self.basicNumberStep), self.basicNumberMax
            )
            val = expected * self.basicNumberScale

        self.dps[self.basicNumberDps] = val
        self.assertEqual(self.basicNumber.native_value, expected)

    async def test_number_set_value(self):
        if self.basicNumberTestData:
            dps_val = self.basicNumberTestData[0]
            val = self.basicNumberTestData[1]
        else:
            val = min(
                max(self.basicNumberMin, self.basicNumberStep),
                self.basicNumberMax,
            )
            dps_val = val * self.basicNumberScale

        async with assert_device_properties_set(
            self.basicNumber._device, {self.basicNumberDps: dps_val}
        ):
            await self.basicNumber.async_set_native_value(val)

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
        self.multiNumberTestData = {}
        self.multiNumberDevClass = {}

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
            self.multiNumberTestData[name] = n.get("testdata", None)
            self.multiNumberDevClass[name] = n.get("device_class", None)

    def test_multi_number_min_value(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.native_min_value,
                self.multiNumberMin[key],
                f"{key} min value mismatch",
            )

    def test_multi_number_max_value(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.native_max_value,
                self.multiNumberMax[key],
                f"{key} max value mismatch",
            )

    def test_multi_number_step(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.native_step,
                self.multiNumberStep[key],
                f"{key} step mismatch",
            )

    def test_multi_number_mode(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.mode,
                self.multiNumberMode[key],
                f"{key} mode mismatch",
            )

    def test_multi_number_unit_of_measurement(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.native_unit_of_measurement,
                self.multiNumberUnit[key],
                f"{key} unit mismatch",
            )

    def test_multi_number_device_class(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.device_class,
                self.multiNumberDevClass[key],
                f"{key} device class mismatch",
            )

    def test_multi_number_value(self):
        for key, subject in self.multiNumber.items():
            if self.multiNumberTestData[key]:
                val = self.multiNumberTestData[key][1]
                dps_val = self.multiNumberTestData[key][0]
            else:
                val = min(
                    max(self.multiNumberMin[key], self.multiNumberStep[key]),
                    self.multiNumberMax[key],
                )
                dps_val = val * self.multiNumberScale[key]

            self.dps[self.multiNumberDps[key]] = dps_val
            self.assertEqual(subject.native_value, val, f"{key} value mismatch")

    async def test_multi_number_set_value(self):
        for key, subject in self.multiNumber.items():
            if self.multiNumberTestData[key]:
                val = self.multiNumberTestData[key][1]
                dps_val = self.multiNumberTestData[key][0]
            else:
                val = min(
                    max(self.multiNumberMin[key], self.multiNumberStep[key]),
                    self.multiNumberMax[key],
                )
                dps_val = val * self.multiNumberScale[key]

            async with assert_device_properties_set(
                subject._device,
                {self.multiNumberDps[key]: dps_val},
                f"{key} failed to set correct value",
            ):
                await subject.async_set_native_value(val)

    def test_multi_number_extra_state_attributes(self):
        for key, subject in self.multiNumber.items():
            self.assertEqual(
                subject.extra_state_attributes,
                {},
                f"{key} extra_state_attributes mismatch",
            )
