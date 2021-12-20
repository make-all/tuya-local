from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import EUROM_600v2_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "5"
ERROR_DPS = "7"


class TestEurom600Heater(
    BasicBinarySensorTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("eurom_600_heater_v2.yaml", EUROM_600v2_HEATER_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=0,
            max=37,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=DEVICE_CLASS_PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["binary_sensor_error"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
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

    def test_error_state(self):
        # There are currently no known error states; update this as
        # they are discovered
        self.dps[ERROR_DPS] = "something"
        self.assertEqual(self.subject.extra_state_attributes, {"error": "something"})
        self.dps[ERROR_DPS] = "0"
        self.assertEqual(self.subject.extra_state_attributes, {"error": "OK"})
