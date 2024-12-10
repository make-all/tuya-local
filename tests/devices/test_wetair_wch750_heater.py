from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import WETAIR_WCH750_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.light import DimmableLightTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
PRESET_DPS = "4"
HVACACTION_DPS = "11"
TIMER_DPS = "19"
COUNTDOWN_DPS = "20"
UNKNOWN21_DPS = "21"
BRIGHTNESS_DPS = "101"


class TestWetairWCH750Heater(
    BasicSelectTests,
    BasicSensorTests,
    DimmableLightTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("wetair_wch750_heater.yaml", WETAIR_WCH750_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=10.0,
            max=35.0,
        )
        self.setUpDimmableLight(
            BRIGHTNESS_DPS,
            self.entities.get("light_display"),
            offval="level0",
            tests=[
                ("level1", 85),
                ("level2", 170),
                ("level3", 255),
            ],
        )
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities.get("select_timer"),
            {
                "0h": "cancel",
                "1h": "1h",
                "2h": "2h",
                "3h": "3h",
                "4h": "4h",
                "5h": "5h",
                "6h": "6h",
                "7h": "7h",
                "8h": "8h",
                "9h": "9h",
                "10h": "10h",
                "11h": "11h",
                "12h": "12h",
                "13h": "13h",
                "14h": "14h",
                "15h": "15h",
                "16h": "16h",
                "17h": "17h",
                "18h": "18h",
                "19h": "19h",
                "20h": "20h",
                "21h": "21h",
                "22h": "22h",
                "23h": "23h",
                "24h": "24h",
            },
        )
        self.setUpBasicSensor(
            COUNTDOWN_DPS,
            self.entities.get("sensor_time_remaining"),
            unit=UnitOfTime.MINUTES,
            device_class=SensorDeviceClass.DURATION,
        )
        self.mark_secondary(
            [
                "light_display",
                "select_timer",
                "sensor_time_remaining",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TURN_ON
            ),
        )

    def test_temperatre_unit_retrns_device_temperatre_unit(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_target_temperature_in_af_mode(self):
        self.dps[TEMPERATURE_DPS] = 25
        self.dps[PRESET_DPS] = "mod_antiforst"
        self.assertEqual(self.subject.target_temperature, None)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "mod_antiforst"}
        ):
            await self.subject.async_set_temperature(preset_mode=PRESET_AWAY)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TEMPERATURE_DPS: 25, PRESET_DPS: "mod_max12h"},
        ):
            await self.subject.async_set_temperature(
                preset_mode=PRESET_BOOST, temperature=25
            )

    async def test_set_target_temperature_fails_in_anti_frost(self):
        self.dps[PRESET_DPS] = "mod_antiforst"

        with self.assertRaisesRegex(
            AttributeError, "temperature cannot be set at this time"
        ):
            await self.subject.async_set_target_temperature(25)

    def test_current_temperature_not_supported(self):
        self.assertIsNone(self.subject.current_temperature)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: True},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HVACMODE_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "mod_free"
        self.assertEqual(self.subject.preset_mode, PRESET_COMFORT)

        self.dps[PRESET_DPS] = "mod_max12h"
        self.assertEqual(self.subject.preset_mode, PRESET_BOOST)

        self.dps[PRESET_DPS] = "mod_antiforst"
        self.assertEqual(self.subject.preset_mode, PRESET_AWAY)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["comfort", "boost", "away"])

    async def test_set_preset_mode_to_comfort(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mod_free"},
        ):
            await self.subject.async_set_preset_mode(PRESET_COMFORT)

    async def test_set_preset_mode_to_boost(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mod_max12h"},
        ):
            await self.subject.async_set_preset_mode(PRESET_BOOST)

    async def test_set_preset_mode_to_away(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "mod_antiforst"},
        ):
            await self.subject.async_set_preset_mode(PRESET_AWAY)

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN21_DPS] = 21

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_21": 21,
            },
        )

    def test_light_icon(self):
        self.assertEqual(self.dimmableLight.icon, None)

    async def test_light_brightness_snaps(self):
        async with assert_device_properties_set(
            self.dimmableLight._device,
            {BRIGHTNESS_DPS: "level1"},
        ):
            await self.dimmableLight.async_turn_on(brightness=100)
