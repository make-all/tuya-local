# Mixins for testing climate entities
from math import floor

from ..helpers import assert_device_properties_set


class TargetTemperatureTests:
    def setUpTargetTemperature(self, dps, subject, min=15, max=35, step=1, scale=1):
        self.targetTemp = subject
        self.targetTempDps = dps
        self.targetTempMin = min
        self.targetTempMax = max
        self.targetTempStep = step
        self.targetTempScale = scale

    def test_target_temperature(self):
        self.dps[self.targetTempDps] = 25 * self.targetTempScale
        self.assertEqual(self.targetTemp.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(
            self.targetTemp.target_temperature_step,
            self.targetTempStep / self.targetTempScale,
        )

    def test_minimum_target_temperature(self):
        self.assertEqual(self.targetTemp.min_temp, self.targetTempMin)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.targetTemp.max_temp, self.targetTempMax)

    async def test_legacy_set_temperature_with_temperature(self):
        test_val = floor((self.targetTempMin + self.targetTempMax) / 2)
        async with assert_device_properties_set(
            self.targetTemp._device,
            {self.targetTempDps: test_val * self.targetTempScale},
        ):
            await self.targetTemp.async_set_temperature(temperature=test_val)

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.targetTemp.async_set_temperature(something="else")
        self.targetTemp._device.async_set_property.assert_not_called()

    async def test_set_target_temperature_succeeds_within_valid_range(self):
        test_val = floor((self.targetTempMin + self.targetTempMax) / 2)
        async with assert_device_properties_set(
            self.targetTemp._device,
            {self.targetTempDps: test_val * self.targetTempScale},
        ):
            await self.targetTemp.async_set_target_temperature(test_val)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        test_val = self.targetTempMin - 1
        with self.assertRaisesRegex(
            ValueError,
            f"temperature \\({test_val}\\) must be between {self.targetTempMin} and {self.targetTempMax}",
        ):
            await self.targetTemp.async_set_target_temperature(test_val)
        test_val = self.targetTempMax + 1
        with self.assertRaisesRegex(
            ValueError,
            f"temperature \\({test_val}\\) must be between {self.targetTempMin} and {self.targetTempMax}",
        ):
            await self.targetTemp.async_set_target_temperature(test_val)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        test_val = floor((self.targetTempMin + self.targetTempMax) / 2)
        test_dpsval = test_val * self.targetTempScale
        test_val = (test_dpsval + 0.3) / self.targetTempScale
        async with assert_device_properties_set(
            self.targetTemp._device,
            {self.targetTempDps: test_dpsval},
        ):
            await self.targetTemp.async_set_target_temperature(test_val)
