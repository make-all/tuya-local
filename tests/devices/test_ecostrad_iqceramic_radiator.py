from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import TEMP_CELSIUS

from ..const import ECOSTRAD_IQCERAMIC_RADIATOR_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
PRESET_DPS = "2"
TEMPERATURE_DPS = "16"
CURRENTTEMP_DPS = "24"
CALIB_DPS = "27"
LOCK_DPS = "40"
PIR_DPS = "104"
SYNC_DPS = "107"
WINDOW_DPS = "108"
LIMIT_DPS = "109"


class TestEcostradAccentIqHeater(
    BasicLockTests,
    BasicNumberTests,
    MultiSelectTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "ecostrad_iqceramic_radiator.yaml",
            ECOSTRAD_IQCERAMIC_RADIATOR_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS, self.subject, min=7.0, max=30.0, scale=10, step=5
        )
        self.setUpBasicLock(
            LOCK_DPS,
            self.entities.get("lock_child_lock"),
        )
        self.setUpBasicNumber(
            CALIB_DPS,
            self.entities.get("number_calibration_offset"),
            min=-5,
            max=5,
            unit=TEMP_CELSIUS,
        )
        self.setUpBasicSwitch(
            SYNC_DPS, self.entities.get("switch_time_sync"), testdata=("1", "0")
        )
        self.setUpMultiSelect(
            [
                {
                    "dps": PIR_DPS,
                    "name": "select_pir_timeout",
                    "options": {
                        "15": "15 mins",
                        "30": "30 mins",
                        "45": "45 mins",
                        "60": "60 mins",
                    },
                },
                {
                    "dps": WINDOW_DPS,
                    "name": "select_open_window_detection",
                    "options": {
                        "0": "Off",
                        "60": "60 mins",
                        "90": "90 mins",
                    },
                },
            ]
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "number_calibration_offset",
                "select_open_window_detection",
                "select_pir_timeout",
                "switch_time_sync",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
            ),
        )

    def test_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            self.subject._device.temperature_unit,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 250
        self.assertEqual(self.subject.current_temperature, 25.0)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.OFF, HVACMode.HEAT],
        )

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [
                "Program",
                "ECO",
                "Comfort",
                "Anti-Freeze",
                "Sensor",
                "Pilot Wire",
            ],
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Program")
        self.dps[PRESET_DPS] = "eco"
        self.assertEqual(self.subject.preset_mode, "ECO")
        self.dps[PRESET_DPS] = "hot"
        self.assertEqual(self.subject.preset_mode, "Comfort")
        self.dps[PRESET_DPS] = "cold"
        self.assertEqual(self.subject.preset_mode, "Anti-Freeze")
        self.dps[PRESET_DPS] = "person_infrared_ray"
        self.assertEqual(self.subject.preset_mode, "Sensor")
        self.dps[PRESET_DPS] = "line_control"
        self.assertEqual(self.subject.preset_mode, "Pilot Wire")

    async def test_set_preset_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("Program")

    async def test_set_preset_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "eco"},
        ):
            await self.subject.async_set_preset_mode("ECO")

    async def test_set_preset_to_hot(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "hot"},
        ):
            await self.subject.async_set_preset_mode("Comfort")

    async def test_set_preset_to_cold(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "cold"},
        ):
            await self.subject.async_set_preset_mode("Anti-Freeze")

    async def test_set_preset_to_pir(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "person_infrared_ray"},
        ):
            await self.subject.async_set_preset_mode("Sensor")

    async def test_set_preset_to_line(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "line_control"},
        ):
            await self.subject.async_set_preset_mode("Pilot Wire")

    def test_extra_state_attributes(self):
        self.dps[LIMIT_DPS] = "3"

        self.assertEqual(
            self.subject.extra_state_attributes,
            {"limit_function": "3"},
        )
