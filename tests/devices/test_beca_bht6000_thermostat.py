from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_COMFORT,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
)

from ..const import BECA_BHT6000_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.light import BasicLightTests
from ..mixins.lock import BasicLockTests
from ..mixins.sensor import BasicSensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
HVACMODE_DPS = "4"
PRESET_DPS = "5"
LOCK_DPS = "6"
FLOOR_DPS = "102"
UNKNOWN103_DPS = "103"
UNKNOWN104_DPS = "104"


class TestBecaBHT6000Thermostat(
    BasicLightTests,
    BasicLockTests,
    BasicSensorTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "beca_bht6000_thermostat_c.yaml",
            BECA_BHT6000_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS, self.subject, min=5.0, max=35.0, scale=2
        )
        self.setUpBasicLight(POWER_DPS, self.entities.get("light_display"))
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSensor(
            FLOOR_DPS,
            self.entities.get("sensor_external_temperature"),
            unit=TEMP_CELSIUS,
            device_class=DEVICE_CLASS_TEMPERATURE,
            state_class="measurement",
            testdata=(36, 18),
        )
        self.mark_secondary(["light_display", "lock_child_lock"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE,
        )

    def test_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit,
            self.subject._device.temperature_unit,
        )

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
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)
        self.dps[POWER_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_AUTO)

        self.dps[HVACMODE_DPS] = "1"
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVAC_MODE_HEAT,
                HVAC_MODE_AUTO,
                HVAC_MODE_OFF,
            ],
        )

    def test_extra_state_attributes(self):
        self.dps[FLOOR_DPS] = 45
        self.dps[UNKNOWN103_DPS] = "103"
        self.dps[UNKNOWN104_DPS] = False

        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"floor_temperature": 22.5, "unknown_103": "103", "unknown_104": False},
        )

    def test_icons(self):
        self.dps[POWER_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")

        self.dps[LOCK_DPS] = True
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right-off")
        self.dps[LOCK_DPS] = False
        self.assertEqual(self.basicLock.icon, "mdi:hand-back-right")
