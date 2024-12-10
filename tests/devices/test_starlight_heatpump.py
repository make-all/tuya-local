from homeassistant.components.climate.const import ClimateEntityFeature

from ..const import STARLIGHT_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

TEMPERATURE_DPS = "2"
FLAGS_DPS = "123"


class TestStarLightHeatpump(
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("starlight_heatpump.yaml", STARLIGHT_HEATPUMP_PAYLOAD)
        self.subject = self.entities["climate"]
        self.display_switch = self.entities.get("light_display")
        self.buzzer_switch = self.entities.get("switch_buzzer")
        self.soft_wind_switch = self.entities.get("switch_soft_wind")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16.0,
            max=31.0,
            scale=10,
            step=5,
        )
        self.mark_secondary(
            [
                "binary_sensor_problem",
                "binary_sensor_filter",
                "light_display",
                "sensor_humidity",
                "select_vertical_swing",
                "select_vertical_position",
                "select_horizontal_swing",
                "select_horizontal_position",
                "select_sleep_mode",
                "switch_buzzer",
                "switch_soft_wind",
                "switch_anti_mildew",
                "switch_health",
                "switch_anti_frost",
                "switch_eco_mode",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.SWING_MODE
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TURN_ON
            ),
        )

    def test_display_is_on(self):
        self.dps[FLAGS_DPS] = "0000"
        self.assertFalse(self.display_switch.is_on)
        self.dps[FLAGS_DPS] = "0008"
        self.assertTrue(self.display_switch.is_on)
        self.dps[FLAGS_DPS] = "8001"
        self.assertFalse(self.display_switch.is_on)
        self.dps[FLAGS_DPS] = "8009"
        self.assertTrue(self.display_switch.is_on)

    def test_buzzer_is_on(self):
        self.dps[FLAGS_DPS] = "0008"
        self.assertFalse(self.buzzer_switch.is_on)
        self.dps[FLAGS_DPS] = "0018"
        self.assertTrue(self.buzzer_switch.is_on)
        self.dps[FLAGS_DPS] = "8000"
        self.assertFalse(self.buzzer_switch.is_on)
        self.dps[FLAGS_DPS] = "8010"
        self.assertTrue(self.buzzer_switch.is_on)

    def test_soft_wind_is_on(self):
        self.dps[FLAGS_DPS] = "0000"
        self.assertFalse(self.soft_wind_switch.is_on)
        self.dps[FLAGS_DPS] = "0008"
        self.assertFalse(self.soft_wind_switch.is_on)
        self.dps[FLAGS_DPS] = "8002"
        self.assertTrue(self.soft_wind_switch.is_on)
        self.dps[FLAGS_DPS] = "8008"
        self.assertTrue(self.soft_wind_switch.is_on)

    async def test_turn_on_display(self):
        self.dps[FLAGS_DPS] = "0000"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "0008"}
        ):
            await self.display_switch.async_turn_on()
        self.dps[FLAGS_DPS] = "8001"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "8009"}
        ):
            await self.display_switch.async_turn_on()

    async def test_turn_off_display(self):
        self.dps[FLAGS_DPS] = "0018"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "0010"}
        ):
            await self.display_switch.async_turn_off()
        self.dps[FLAGS_DPS] = "8009"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "8001"}
        ):
            await self.display_switch.async_turn_off()

    async def test_turn_on_buzzer(self):
        self.dps[FLAGS_DPS] = "8008"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "8018"}
        ):
            await self.buzzer_switch.async_turn_on()
        self.dps[FLAGS_DPS] = "0009"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "0019"}
        ):
            await self.buzzer_switch.async_turn_on()

    async def test_turn_off_buzzer(self):
        self.dps[FLAGS_DPS] = "8018"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "8008"}
        ):
            await self.buzzer_switch.async_turn_off()
        self.dps[FLAGS_DPS] = "0019"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "0009"}
        ):
            await self.buzzer_switch.async_turn_off()

    async def test_turn_on_soft_wind(self):
        self.dps[FLAGS_DPS] = "0008"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "8008"}
        ):
            await self.soft_wind_switch.async_turn_on()
        self.dps[FLAGS_DPS] = "0010"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "8010"}
        ):
            await self.soft_wind_switch.async_turn_on()

    async def test_turn_off_soft_wind(self):
        self.dps[FLAGS_DPS] = "8008"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "0008"}
        ):
            await self.soft_wind_switch.async_turn_off()
        self.dps[FLAGS_DPS] = "8011"
        async with assert_device_properties_set(
            self.subject._device, {FLAGS_DPS: "0011"}
        ):
            await self.soft_wind_switch.async_turn_off()
