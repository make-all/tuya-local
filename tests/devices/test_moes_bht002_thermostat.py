from homeassistant.components.climate.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature

from ..const import MOES_BHT002_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.lock import BasicLockTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
PRESET_DPS = "5"
LOCK_DPS = "6"
UNKNOWN104_DPS = "104"


class TestMoesBHT002Thermostat(
    BasicLockTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "moes_bht002_thermostat_c.yaml",
            MOES_BHT002_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5.0,
            max=35.0,
            scale=2,
        )
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.mark_secondary(["lock_child_lock"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TURN_ON
            ),
        )

    def test_temperature_unit(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: True}
        ):
            await self.subject.async_set_temperature(preset_mode=PRESET_ECO)

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                TEMPERATURE_DPS: 44,
                PRESET_DPS: False,
            },
        ):
            await self.subject.async_set_temperature(
                temperature=22, preset_mode=PRESET_COMFORT
            )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 44
        self.assertEqual(self.subject.current_temperature, 22)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = False
        self.dps[HVACMODE_DPS] = "0"
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

        self.dps[POWER_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)

        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.HEAT,
                HVACMode.AUTO,
                HVACMode.OFF,
            ],
        )

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN104_DPS] = False

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"unknown_104": False},
        )
