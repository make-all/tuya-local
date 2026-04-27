from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.humidifier import HumidifierEntityFeature

from ..const import NOVADRY_12SMART_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.lock import BasicLockTests
from ..mixins.select import BasicSelectTests, MultiSelectTests
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
HUMIDITY_DPS = "3"
SPEED_DPS = "4"
MODE_DPS = "5"
CURRENT_HUMIDITY_DPS = "6"
IONIZER_DPS = "10"
CHILDLOCK_DPS = "16"
TIMER_DPS = "17"
FAULT_DPS = "19"


class TestNovaDry12SmartDehumidifier(
    BasicBinarySensorTests,
    BasicLockTests,
    BasicSelectTests,
    MultiSelectTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    def setUp(self):
        self.setUpForConfig(
            "novadry_12smart_dehumidifier.yaml",
            NOVADRY_12SMART_DEHUMIDIFIER_PAYLOAD,
        )
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicBinarySensor(
            FAULT_DPS,
            self.entities.get("binary_sensor_tank_full"),
            device_class=None,
            testdata=(1, 0),
        )
        self.setUpBasicLock(
            CHILDLOCK_DPS,
            self.entities.get("lock_child_lock"),
        )
        self.setUpBasicSelect(
            SPEED_DPS,
            self.entities.get("select_speed"),
            {"1": "low", "2": "high"},
        )
        self.setUpMultiSelect(
            [
                {
                    "name": "select_timer",
                    "dps": TIMER_DPS,
                    "options": {
                        "0h": "cancel",
                        "1h": "1h",
                        "2h": "2h",
                        "3h": "3h",
                    },
                }
            ]
        )
        self.mark_secondary(
            [
                "select_speed",
                "select_timer",
                "switch_ionizer",
                "lock_child_lock",
                "binary_sensor_tank_full",
                "binary_sensor_problem",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            HumidifierEntityFeature.MODES,
        )

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = "45"
        self.assertEqual(self.subject.target_humidity, 45)
        self.dps[HUMIDITY_DPS] = "60"
        self.assertEqual(self.subject.target_humidity, 60)

    def test_min_max_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)
        self.assertEqual(self.subject.max_humidity, 80)

    async def test_set_humidity(self):
        async with assert_device_properties_set(
            self.subject._device, {HUMIDITY_DPS: "50"}
        ):
            await self.subject.async_set_humidity(50)

    def test_current_humidity(self):
        self.dps[CURRENT_HUMIDITY_DPS] = 68
        self.assertEqual(self.subject.current_humidity, 68)

    def test_mode(self):
        self.dps[MODE_DPS] = "dehumidify"
        self.assertEqual(self.subject.mode, "dehumidify")
        self.dps[MODE_DPS] = "drying"
        self.assertEqual(self.subject.mode, "laundry")
        self.dps[MODE_DPS] = "continuous"
        self.assertEqual(self.subject.mode, "continuous")

    def test_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            ["dehumidify", "laundry", "continuous"],
        )

    async def test_set_mode_dehumidify(self):
        async with assert_device_properties_set(
            self.subject._device, {MODE_DPS: "dehumidify"}
        ):
            await self.subject.async_set_mode("dehumidify")

    async def test_set_mode_laundry(self):
        async with assert_device_properties_set(
            self.subject._device, {MODE_DPS: "drying"}
        ):
            await self.subject.async_set_mode("laundry")

    async def test_set_mode_continuous(self):
        async with assert_device_properties_set(
            self.subject._device, {MODE_DPS: "continuous"}
        ):
            await self.subject.async_set_mode("continuous")

    def test_ionizer(self):
        self.dps[IONIZER_DPS] = True
        self.assertTrue(self.entities.get("switch_ionizer").is_on)
        self.dps[IONIZER_DPS] = False
        self.assertFalse(self.entities.get("switch_ionizer").is_on)

    async def test_set_ionizer_on(self):
        async with assert_device_properties_set(
            self.entities.get("switch_ionizer")._device, {IONIZER_DPS: True}
        ):
            await self.entities.get("switch_ionizer").async_turn_on()

    async def test_set_ionizer_off(self):
        async with assert_device_properties_set(
            self.entities.get("switch_ionizer")._device, {IONIZER_DPS: False}
        ):
            await self.entities.get("switch_ionizer").async_turn_off()

    def test_tank_full_is_on(self):
        self.dps[FAULT_DPS] = 1
        self.assertTrue(self.entities.get("binary_sensor_tank_full").is_on)
        self.dps[FAULT_DPS] = 0
        self.assertFalse(self.entities.get("binary_sensor_tank_full").is_on)

    def test_problem_sensor_is_off_when_no_fault(self):
        self.dps[FAULT_DPS] = 0
        self.assertFalse(self.entities.get("binary_sensor_problem").is_on)

    def test_problem_sensor_is_off_when_tank_full_only(self):
        self.dps[FAULT_DPS] = 1
        self.assertFalse(self.entities.get("binary_sensor_problem").is_on)

    def test_problem_sensor_is_on_when_other_fault(self):
        self.dps[FAULT_DPS] = 2
        self.assertTrue(self.entities.get("binary_sensor_problem").is_on)
        self.dps[FAULT_DPS] = 4
        self.assertTrue(self.entities.get("binary_sensor_problem").is_on)

    def test_extra_state_attributes_description(self):
        problem = self.entities.get("binary_sensor_problem")
        self.dps[FAULT_DPS] = 0
        self.assertEqual(problem.extra_state_attributes.get("description"), "ok")
        self.dps[FAULT_DPS] = 1
        self.assertEqual(
            problem.extra_state_attributes.get("description"),
            "Water Tank Full or Removed",
        )
        self.dps[FAULT_DPS] = 2
        self.assertEqual(problem.extra_state_attributes.get("description"), "E2")
