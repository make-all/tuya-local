from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    TIME_MINUTES,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from ..const import DEVOLA_PATIO_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
MODE_DPS = "4"
POWERLEVEL_DPS = "5"
PRESET_DPS = "6"
LOCK_DPS = "7"
TIMER_DPS = "12"
HVACACTION_DPS = "14"
UNIT_DPS = "19"
TEMPF_DPS = "20"
CURTEMPF_DPS = "21"


class TestDevolaPatioHeater(
    BasicLockTests,
    BasicNumberTests,
    MultiSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("devola_patio_heater.yaml", DEVOLA_PATIO_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5,
            max=45,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=1440,
            step=1.0,
            unit=TIME_MINUTES,
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": POWERLEVEL_DPS,
                    "name": "sensor_power_level",
                    "unit": PERCENTAGE,
                    "device_class": SensorDeviceClass.POWER_FACTOR,
                    "testdata": ("2", 50),
                },
                {
                    "dps": MODE_DPS,
                    "name": "sensor_mode",
                    "testdata": ("test", "test"),
                },
            ],
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "number_timer",
                "sensor_power_level",
                "sensor_mode",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
            ),
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:fire")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:fire-off")

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(
            self.subject.temperature_unit,
            TEMP_CELSIUS,
        )
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(
            self.subject.temperature_unit,
            TEMP_FAHRENHEIT,
        )

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: True}
        ):
            await self.subject.async_set_temperature(preset_mode="Eco")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 22,
                PRESET_DPS: True,
            },
        ):
            await self.subject.async_set_temperature(temperature=22, preset_mode="Eco")

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_current_temperature_redirects_in_f(self):
        self.dps[CURRENTTEMP_DPS] = 24
        self.dps[CURTEMPF_DPS] = 75
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.current_temperature, 75)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

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

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = False
        self.assertEqual(self.subject.preset_mode, "Normal")

        self.dps[PRESET_DPS] = True
        self.assertEqual(self.subject.preset_mode, "Eco")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(self.subject.preset_modes, ["Normal", "Eco"])

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: False},
        ):
            await self.subject.async_set_preset_mode("Normal")

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: True},
        ):
            await self.subject.async_set_preset_mode("Eco")
