from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import BWT_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
ERROR_DPS = "9"


class TestBWTHeatpump(
    BasicBinarySensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("bwt_heatpump.yaml", BWT_HEATPUMP_PAYLOAD)
        self.subject = self.entities["climate"]
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5,
            max=40,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_water_flow"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["binary_sensor_water_flow"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:hot-tub")
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "cool"}
        ):
            await self.subject.async_set_temperature(preset_mode="Smart Cooling")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 26, PRESET_DPS: "heat"}
        ):
            await self.subject.async_set_temperature(
                temperature=26, preset_mode="Smart Heating"
            )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "heat"
        self.assertEqual(self.subject.preset_mode, "Smart Heating")

        self.dps[PRESET_DPS] = "cool"
        self.assertEqual(self.subject.preset_mode, "Smart Cooling")

        self.dps[PRESET_DPS] = "quickheat"
        self.assertEqual(self.subject.preset_mode, "Boost Heating")

        self.dps[PRESET_DPS] = "quickcool"
        self.assertEqual(self.subject.preset_mode, "Boost Cooling")

        self.dps[PRESET_DPS] = "quietheat"
        self.assertEqual(self.subject.preset_mode, "Eco Heating")

        self.dps[PRESET_DPS] = "quietcool"
        self.assertEqual(self.subject.preset_mode, "Eco Cooling")

        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Auto")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [
                "Smart Heating",
                "Boost Heating",
                "Eco Heating",
                "Smart Cooling",
                "Boost Cooling",
                "Eco Cooling",
                "Auto",
            ],
        )

    async def test_set_preset_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "heat"},
        ):
            await self.subject.async_set_preset_mode("Smart Heating")

    async def test_set_preset_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "cool"},
        ):
            await self.subject.async_set_preset_mode("Smart Cooling")

    async def test_set_preset_mode_to_quickheat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quickheat"},
        ):
            await self.subject.async_set_preset_mode("Boost Heating")

    async def test_set_preset_mode_to_quickcool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quickcool"},
        ):
            await self.subject.async_set_preset_mode("Boost Cooling")

    async def test_set_preset_mode_to_quietheat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quietheat"},
        ):
            await self.subject.async_set_preset_mode("Eco Heating")

    async def test_set_preset_mode_to_quietcool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "quietcool"},
        ):
            await self.subject.async_set_preset_mode("Eco Cooling")

    async def test_set_preset_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("Auto")

    def test_error_state(self):
        self.dps[ERROR_DPS] = 0
        self.assertEqual(self.subject.extra_state_attributes, {"error": "OK"})

        self.dps[ERROR_DPS] = 1
        self.assertEqual(
            self.subject.extra_state_attributes,
            {"error": "Water Flow Protection"},
        )
        self.dps[ERROR_DPS] = 2
        self.assertEqual(
            self.subject.extra_state_attributes,
            {"error": 2},
        )
