from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, UnitOfTime

from ..const import GECO_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
LOCK_DPS = "2"
TEMPERATURE_DPS = "3"
CURRENTTEMP_DPS = "4"
TIMER_DPS = "5"
ERROR_DPS = "6"


class TestGoldairGECOHeater(
    BasicBinarySensorTests,
    BasicLockTests,
    BasicNumberTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("goldair_geco_heater.yaml", GECO_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=15.0,
            max=35.0,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=24,
            unit=UnitOfTime.HOURS,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(
            [
                "lock_child_lock",
                "number_timer",
                "binary_sensor_problem",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

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

    def test_extra_state_attributes(self):
        # There are currently no known error states; update this as
        # they are discovered
        self.dps[ERROR_DPS] = "something"
        self.dps[TIMER_DPS] = 10
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"error": "something", "timer": 10},
        )
        self.dps[ERROR_DPS] = "0"
        self.dps[TIMER_DPS] = 0
        self.assertDictEqual(
            self.subject.extra_state_attributes, {"error": "OK", "timer": 0}
        )
