# Mixins for testing time entities
from datetime import time

from ..helpers import assert_device_properties_set


class BasicTimeTests:
    def setUpBasicTime(
        self,
        subject,
        hour_dp=None,
        minute_dp=None,
        second_dp=None,
        testdata=None,
    ):
        self.basicTime = subject
        self.basicTimeHourDp = hour_dp
        self.basicTimeMinDp = minute_dp
        self.basicTimeSecDp = second_dp
        self.basicTimeTestData = testdata

    def test_time_value(self):
        if self.basicTimeTestData:
            hour = self.basicTimeTestData["hour"]
            minute = self.basicTimeTestData["minute"]
            second = self.basicTimeTestData["second"]
            expected = self.basicTimeTestData["time"]
        else:
            expected = "00:00:00"
            hour = minute = second = 0

        if self.basicTimeHourDp:
            self.dps[self.basicTimeHourDp] = hour
        if self.basicTimeMinDp:
            self.dps[self.basicTimeMinDp] = minute
        if self.basicTimeSecDp:
            self.dps[self.basicTimeSecDp] = second
        self.assertEqual(self.basicTime.native_value.isoformat("seconds"), expected)

    async def test_time_set_value(self):
        if self.basicTimeTestData:
            hour = self.basicTimeTestData["hour"]
            minute = self.basicTimeTestData["minute"]
            second = self.basicTimeTestData["second"]
            val = self.basicTimeTestData["time"]
        else:
            val = "00:00:00"
            hour = minute = second = 0

        expected = {}
        if self.basicTimeHourDp:
            expected[self.basicTimeHourDp] = hour
        if self.basicTimeMinDp:
            expected[self.basicTimeMinDp] = minute
        if self.basicTimeSecDp:
            expected[self.basicTimeSecDp] = second

        async with assert_device_properties_set(
            self.basicTime._device,
            expected,
            f"{self.basicTime.name} failed to set correct value",
        ):
            await self.basicTime.async_set_native_value(time.fromisoformat(val))


class MultiTimeTests:
    def setUpMultiTime(self, times):
        self.multiTime = {}
        self.multiTimeHourDp = {}
        self.multiTimeMinDp = {}
        self.multiTimeSecDp = {}
        self.multiTimeTestData = {}

        for t in times:
            name = t.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No time for {name} found.")
            self.multiTime[name] = subject
            self.multiTimeHourDp[name] = t.get("hour")
            self.multiTimeMinDp[name] = t.get("minute")
            self.multiTimeSecDp[name] = t.get("second")
            self.multiTimeTestData[name] = t.get("testdata", None)

    def test_multi_time_value(self):
        for key, subject in self.multiTime.items():
            if self.multiTimeTestData[key]:
                hour = self.multiTimeTestData[key].get("hour", 0)
                minute = self.multiTimeTestData[key].get("minute", 0)
                second = self.multiTimeTestData[key].get("second", 0)
                expected = self.multiTimeTestData[key].get("time")
            else:
                expected = "00:00:00"
                hour = minute = second = 0

            if self.multiTimeHourDp[key]:
                self.dps[self.multiTimeHourDp[key]] = hour
            if self.multiTimeMinDp[key]:
                self.dps[self.multiTimeMinDp[key]] = minute
            if self.multiTimeSecDp[key]:
                self.dps[self.multiTimeSecDp[key]] = second
            self.assertEqual(
                subject.native_value.isoformat("seconds"),
                expected,
                f"{key} value mismatch",
            )

    async def test_multi_time_set_value(self):
        for key, subject in self.multiTime.items():
            if self.multiTimeTestData[key]:
                hour = self.multiTimeTestData[key].get("hour", 0)
                minute = self.multiTimeTestData[key].get("minute", 0)
                second = self.multiTimeTestData[key].get("second", 0)
                val = self.multiTimeTestData[key].get("time")
            else:
                val = "00:00:00"
                hour = minute = second = 0

            expected = {}
            if self.multiTimeHourDp[key]:
                expected[self.multiTimeHourDp[key]] = hour
            if self.multiTimeMinDp[key]:
                expected[self.multiTimeMinDp[key]] = minute
            if self.multiTimeSecDp[key]:
                expected[self.multiTimeSecDp[key]] = second
            async with assert_device_properties_set(
                subject._device,
                expected,
                f"{key} failed to set correct value",
            ):
                await subject.async_set_value(time.fromisoformat(val))
