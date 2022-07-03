from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE

from ..const import ORION_SMARTLOCK_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

ULFP_DP = "1"
ULPWD_DP = "2"
ULTMP_DP = "3"
ULDYN_DP = "4"
ULCARD_DP = "5"
ERROR_DP = "8"
REQUEST_DP = "9"
APPROVE_DP = "10"
BATTERY_DP = "12"
ULAPP_DP = "15"
DURESS_DP = "16"


class TestOrionSmartLock(
    MultiBinarySensorTests,
    MultiSensorTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("orion_smart_lock.yaml", ORION_SMARTLOCK_PAYLOAD)
        self.subject = self.entities.get("lock")
        self.setUpMultiBinarySensors(
            [
                {
                    "dps": ERROR_DP,
                    "name": "binary_sensor_tampered",
                    "device_class": BinarySensorDeviceClass.TAMPER,
                    "testdata": (33, 0),
                },
                {
                    "dps": DURESS_DP,
                    "name": "binary_sensor_duress",
                    "device_class": BinarySensorDeviceClass.SAFETY,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "dps": ERROR_DP,
                    "name": "sensor_alert",
                    "testdata": (512, "key_left_in"),
                },
                {
                    "dps": BATTERY_DP,
                    "name": "sensor_battery",
                    "device_class": SensorDeviceClass.BATTERY,
                    "unit": PERCENTAGE,
                },
            ]
        )
        self.mark_secondary(["sensor_alert"])

    def test_is_locked(self):
        # Default is all 0
        self.assertTrue(self.subject.is_locked)
        self.dps[ULFP_DP] = 1
        self.assertFalse(self.subject.is_locked)
        self.dps[ULFP_DP] = 0
        self.dps[ULPWD_DP] = 2
        self.assertFalse(self.subject.is_locked)
        self.dps[ULPWD_DP] = 0
        self.dps[ULTMP_DP] = 3
        self.assertFalse(self.subject.is_locked)
        self.dps[ULTMP_DP] = 0
        self.dps[ULDYN_DP] = 4
        self.assertFalse(self.subject.is_locked)
        self.dps[ULDYN_DP] = 0
        self.dps[ULCARD_DP] = 5
        self.assertFalse(self.subject.is_locked)
        self.dps[ULCARD_DP] = 0
        self.dps[ULAPP_DP] = 6
        self.assertFalse(self.subject.is_locked)

    def test_is_jammed(self):
        self.assertFalse(self.subject.is_jammed)
        self.dps[ERROR_DP] = 1
        self.assertFalse(self.subject.is_jammed)
        self.dps[ERROR_DP] = 16
        self.assertTrue(self.subject.is_jammed)
        self.dps[ERROR_DP] = 128
        self.assertTrue(self.subject.is_jammed)
        self.dps[ERROR_DP] = 17
        self.assertTrue(self.subject.is_jammed)
        self.dps[ERROR_DP] = 144
        self.assertTrue(self.subject.is_jammed)

    def test_changed_by(self):
        self.dps[ULFP_DP] = 1
        self.assertEqual(self.subject.changed_by, "Finger #1")
        self.dps[ULFP_DP] = 0
        self.dps[ULPWD_DP] = 2
        self.assertEqual(self.subject.changed_by, "Password #2")
        self.dps[ULPWD_DP] = 0
        self.dps[ULTMP_DP] = 3
        self.assertEqual(self.subject.changed_by, "Temporary Password #3")
        self.dps[ULTMP_DP] = 0
        self.dps[ULDYN_DP] = 4
        self.assertEqual(self.subject.changed_by, "Dynamic Password #4")
        self.dps[ULDYN_DP] = 0
        self.dps[ULCARD_DP] = 5
        self.assertEqual(self.subject.changed_by, "Card #5")
        self.dps[ULCARD_DP] = 0
        self.dps[ULAPP_DP] = 6
        self.assertEqual(self.subject.changed_by, "App #6")

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})

    async def test_unlock(self):
        self.dps[REQUEST_DP] = 30
        async with assert_device_properties_set(
            self.subject._device, {APPROVE_DP: True}
        ):
            await self.subject.async_unlock()

    async def test_unlock_fails_when_not_requested(self):
        self.dps[REQUEST_DP] = 0
        with self.assertRaises(TimeoutError):
            await self.subject.async_unlock()
