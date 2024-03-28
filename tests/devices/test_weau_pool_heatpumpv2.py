from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode

from ..const import WEAU_POOL_HEATPUMPV2_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
MODE_DPS = "2"
TEMPERATURE_DPS = "9"
CURRENTTEMP_DPS = "10"
FAULT_DPS = "20"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"
UNKNOWN103_DPS = "103"
UNKNOWN104_DPS = "104"


class TestWeauPoolHeatpumpV2(
    BasicBinarySensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("weau_pool_heatpump_v2.yaml", WEAU_POOL_HEATPUMPV2_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=7.0,
            max=60.0,
        )
        self.setUpBasicBinarySensor(
            FAULT_DPS,
            self.entities.get("binary_sensor_problem"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(4, 0),
        )
        self.mark_secondary(["binary_sensor_problem"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON,
        )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 194
        self.assertEqual(self.subject.current_temperature, 19.4)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[MODE_DPS] = "eheat"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[MODE_DPS] = "ecool"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[MODE_DPS] = "sheat"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[MODE_DPS] = "scool"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[MODE_DPS] = "bheat"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[MODE_DPS] = "bcool"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.HEAT_COOL],
        )

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    async def test_set_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, MODE_DPS: "ecool"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True, MODE_DPS: "eheat"},
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    def test_extra_state_attributes(self):
        self.dps[FAULT_DPS] = 4
        self.dps[UNKNOWN101_DPS] = 101
        self.dps[UNKNOWN102_DPS] = 102
        self.dps[UNKNOWN103_DPS] = 103
        self.dps[UNKNOWN104_DPS] = True
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "fault": "flow_fault",
                "unknown_101": 101,
                "unknown_102": 102,
                "unknown_103": 103,
                "unknown_104": True,
            },
        )
