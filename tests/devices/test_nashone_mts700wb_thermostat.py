from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TIME_MINUTES,
)

from ..const import NASHONE_MTS700WB_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.number import BasicNumberTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
HVACMODE_DPS = "2"
HVACACTION_DPS = "3"
TEMPERATURE_DPS = "16"
TEMPF_DPS = "17"
UNIT_DPS = "23"
CURRENTTEMP_DPS = "24"
CALIBOFFSET_DPS = "27"
CURRTEMPF_DPS = "29"
RESET_DPS = "39"
TIMER_DPS = "41"
COUNTDOWN_DPS = "42"


class TestNashoneMTS700WBThermostat(
    BasicNumberTests,
    BasicSelectTests,
    BasicSensorTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "nashone_mts700wb_thermostat.yaml",
            NASHONE_MTS700WB_THERMOSTAT_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=-20,
            max=105,
        )
        self.setUpBasicNumber(
            CALIBOFFSET_DPS,
            self.entities.get("number_calibration_offset"),
            min=-5,
            max=5,
        )
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities.get("select_timer"),
            {
                "cancel": "off",
                "1h": "1 hour",
            },
        )
        self.setUpBasicSensor(
            COUNTDOWN_DPS,
            self.entities.get("sensor_timer"),
            unit=TIME_MINUTES,
            testdata=(600, 10.0),
        )
        self.setUpBasicSwitch(
            RESET_DPS,
            self.entities.get("switch_factory_reset"),
        )
        self.mark_secondary(
            [
                "number_calibration_offset",
                "select_timer",
                "sensor_timer",
                "switch_factory_reset",
            ],
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 24
        self.assertEqual(self.subject.current_temperature, 24)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "hot"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.COOL,
                HVACMode.HEAT,
                HVACMode.OFF,
            ],
        )

    async def test_set_hvac_mode_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "cold"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, HVACMODE_DPS: "hot"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    def test_hvac_action(self):
        self.dps[HVACMODE_DPS] = "hot"
        self.dps[HVACACTION_DPS] = "manual"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)
        self.dps[HVACMODE_DPS] = "cold"
        self.assertEqual(self.subject.hvac_action, HVACAction.COOLING)

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})

    def test_icons(self):
        self.assertEqual(self.basicNumber.icon, "mdi:arrow-collapse-up")
        self.assertEqual(self.basicSelect.icon, "mdi:timer")
        self.assertEqual(self.basicSensor.icon, "mdi:timer")
        self.assertEqual(self.basicSwitch.icon, "mdi:cog-refresh")
