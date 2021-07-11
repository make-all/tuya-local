from homeassistant.components.fan import SUPPORT_PRESET_MODE
from homeassistant.components.humidifier import SUPPORT_MODES
from homeassistant.const import STATE_UNAVAILABLE

from ..const import ELECTRIQ_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
MODE_DPS = "2"
CURRENTHUMID_DPS = "3"
HUMIDITY_DPS = "4"
LOCK_DPS = "7"
LIGHT_DPS = "10"
PRESET_DPS = "102"
CURRENTTEMP_DPS = "103"
IONIZER_DPS = "104"


class TestElectriqDehumidifier(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("electriq_dehumidifier.yaml", ELECTRIQ_DEHUMIDIFIER_PAYLOAD)
        self.subject = self.entities.get("humidifier")
        self.fan = self.entities.get("fan")
        self.light = self.entities.get("light")
        self.lock = self.entities.get("lock")
        self.switch = self.entities.get("switch")

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_MODES)
        self.assertEqual(self.fan.supported_features, SUPPORT_PRESET_MODE)

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[MODE_DPS] = "fan"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-purifier")

        self.dps[MODE_DPS] = "high"
        self.assertEqual(self.subject.icon, "mdi:tshirt-crew-outline")

        self.assertEqual(self.light.icon, "mdi:solar-power")
        self.assertEqual(self.switch.icon, "mdi:creation")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 35)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    async def test_set_target_humidity_rounds_up_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 55},
        ):
            await self.subject.async_set_humidity(53)

    async def test_set_target_humidity_rounds_down_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 50},
        ):
            await self.subject.async_set_humidity(52)

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

    def test_mode(self):
        self.dps[MODE_DPS] = "low"
        self.assertEqual(self.subject.mode, "Low")
        self.dps[MODE_DPS] = "high"
        self.assertEqual(self.subject.mode, "High")
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.mode, "Auto")
        self.dps[MODE_DPS] = "fan"
        self.assertEqual(self.subject.mode, "Air clean")

    async def test_set_mode_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "auto",
            },
        ):
            await self.subject.async_set_mode("Auto")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "low",
            },
        ):
            await self.subject.async_set_mode("Low")
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

    async def test_set_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "fan",
            },
        ):
            await self.subject.async_set_mode("Air clean")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_fan_preset_mode(self):
        self.dps[PRESET_DPS] = "45"
        self.assertEqual(self.fan.preset_mode, "Half open")

        self.dps[PRESET_DPS] = "90"
        self.assertEqual(self.fan.preset_mode, "Fully open")

        self.dps[PRESET_DPS] = "0_90"
        self.assertEqual(self.fan.preset_mode, "Oscillate")

    async def test_set_fan_to_half_open(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "45",
            },
        ):
            await self.fan.async_set_preset_mode("Half open")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_fan_to_fully_open(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "90",
            },
        ):
            await self.fan.async_set_preset_mode("Fully open")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_fan_to_oscillate(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PRESET_DPS: "0_90",
            },
        ):
            await self.fan.async_set_preset_mode("Oscillate")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_lock_is_locked(self):
        self.dps[LOCK_DPS] = True
        self.assertTrue(self.lock.is_locked)

        self.dps[LOCK_DPS] = False
        self.assertFalse(self.lock.is_locked)

        self.dps[LOCK_DPS] = None
        self.assertFalse(self.lock.is_locked)

    async def test_lock_locks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: True}):
            await self.lock.async_lock()

    async def test_lock_unlocks(self):
        async with assert_device_properties_set(self.lock._device, {LOCK_DPS: False}):
            await self.lock.async_unlock()

    def test_light_is_on(self):
        self.dps[LIGHT_DPS] = True
        self.assertTrue(self.light.is_on)

        self.dps[LIGHT_DPS] = False
        self.assertFalse(self.light.is_on)

    async def test_light_turn_on(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_turn_off()

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[LIGHT_DPS] = False
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: True}):
            await self.light.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[LIGHT_DPS] = True
        async with assert_device_properties_set(self.light._device, {LIGHT_DPS: False}):
            await self.light.async_toggle()

    def test_switch_is_on(self):
        self.dps[IONIZER_DPS] = True
        self.assertTrue(self.switch.is_on)

        self.dps[IONIZER_DPS] = False
        self.assertFalse(self.switch.is_on)

    async def test_switch_turn_on(self):
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: True}
        ):
            await self.switch.async_turn_on()

    async def test_switch_turn_off(self):
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: False}
        ):
            await self.switch.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[IONIZER_DPS] = False
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: True}
        ):
            await self.switch.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[IONIZER_DPS] = True
        async with assert_device_properties_set(
            self.switch._device, {IONIZER_DPS: False}
        ):
            await self.switch.async_toggle()

    def test_state_attributes(self):
        self.dps[CURRENTHUMID_DPS] = 50
        self.dps[CURRENTTEMP_DPS] = 21
        self.assertCountEqual(
            self.subject.device_state_attributes,
            {"current_humidity": 50, "current_temperature": 21},
        )
        self.assertEqual(self.fan.device_state_attributes, {})
        self.assertEqual(self.light.device_state_attributes, {})
        self.assertEqual(self.lock.device_state_attributes, {})
        self.assertEqual(self.switch.device_state_attributes, {})
