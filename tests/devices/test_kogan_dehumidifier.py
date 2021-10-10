from homeassistant.components.fan import SUPPORT_OSCILLATE, SUPPORT_SET_SPEED
from homeassistant.components.humidifier import SUPPORT_MODES
from homeassistant.const import STATE_UNAVAILABLE

from ..const import KOGAN_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
MODE_DPS = "2"
CURRENTHUMID_DPS = "3"
SWING_DPS = "8"
ERROR_DPS = "11"
TIMER_DPS = "12"
COUNTDOWN_DPS = "13"
HUMIDITY_DPS = "101"


class TestKoganDehumidifier(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("kogan_dehumidifier.yaml", KOGAN_DEHUMIDIFIER_PAYLOAD)
        self.subject = self.entities.get("humidifier")
        self.fan = self.entities.get("fan")

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_MODES)
        self.assertEqual(
            self.fan.supported_features,
            SUPPORT_OSCILLATE | SUPPORT_SET_SPEED,
        )

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "low"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[MODE_DPS] = "quickdry"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:tshirt-crew-outline")

        self.dps[ERROR_DPS] = 1
        self.assertEqual(self.subject.icon, "mdi:cup-water")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 0)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    def test_is_on(self):
        self.dps[SWITCH_DPS] = True
        self.assertTrue(self.subject.is_on)
        self.assertTrue(self.fan.is_on)

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)
        self.assertFalse(self.fan.is_on)

        self.dps[SWITCH_DPS] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)
        self.assertEqual(self.fan.is_on, STATE_UNAVAILABLE)

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

    async def test_fan_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.fan.async_turn_on()

    async def test_fan_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.fan.async_turn_off()

    def test_modes(self):
        self.assertCountEqual(
            self.subject.available_modes,
            [
                "Low",
                "Medium",
                "High",
                "Dry Clothes",
            ],
        )

    def test_mode(self):
        self.dps[MODE_DPS] = "low"
        self.assertEqual(self.subject.mode, "Low")
        self.dps[MODE_DPS] = "middle"
        self.assertEqual(self.subject.mode, "Medium")
        self.dps[MODE_DPS] = "high"
        self.assertEqual(self.subject.mode, "High")
        self.dps[MODE_DPS] = "quickdry"
        self.assertEqual(self.subject.mode, "Dry Clothes")

    async def test_set_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "low",
            },
        ):
            await self.subject.async_set_mode("Low")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "middle",
            },
        ):
            await self.subject.async_set_mode("Medium")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "high",
            },
        ):
            await self.subject.async_set_mode("High")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_clothes(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "quickdry",
            },
        ):
            await self.subject.async_set_mode("Dry Clothes")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_fan_speed_steps(self):
        self.assertEqual(self.fan.speed_count, 3)

    def test_fan_speed(self):
        self.dps[MODE_DPS] = "low"
        self.assertAlmostEqual(self.fan.percentage, 33.3, 1)
        self.dps[MODE_DPS] = "middle"
        self.assertAlmostEqual(self.fan.percentage, 66.7, 1)
        self.dps[MODE_DPS] = "high"
        self.assertEqual(self.fan.percentage, 100)
        self.dps[MODE_DPS] = "quickdry"
        self.assertEqual(self.fan.percentage, 100)

    async def test_fan_set_speed_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "low",
            },
        ):
            await self.fan.async_set_percentage(33)

    async def test_fan_set_speed_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "middle",
            },
        ):
            await self.fan.async_set_percentage(66)

    async def test_fan_set_speed_to_high(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "high",
            },
        ):
            await self.fan.async_set_percentage(100)

    def test_fan_oscillating(self):
        self.dps[SWING_DPS] = True
        self.assertTrue(self.fan.oscillating)

        self.dps[SWING_DPS] = False
        self.assertFalse(self.fan.oscillating)

    async def test_set_fan_oscillate_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SWING_DPS: True,
            },
        ):
            await self.fan.async_oscillate(True)
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_fan_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SWING_DPS: False,
            },
        ):
            await self.fan.async_oscillate(False)
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_device_state_attributes(self):
        self.dps[CURRENTHUMID_DPS] = 55
        self.dps[ERROR_DPS] = 1
        self.dps[TIMER_DPS] = 3
        self.dps[COUNTDOWN_DPS] = 160
        self.assertDictEqual(
            self.subject.device_state_attributes,
            {
                "current_humidity": 55,
                "error": "Tank full",
                "timer_hr": 3,
                "timer": 160,
            },
        )
        self.assertEqual(self.fan.device_state_attributes, {})
