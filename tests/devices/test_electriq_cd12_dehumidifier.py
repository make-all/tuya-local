from homeassistant.components.humidifier import SUPPORT_MODES
from homeassistant.components.light import COLOR_MODE_ONOFF

from ..const import ELECTRIQ_CD12PW_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
MODE_DPS = "2"
CURRENTHUMID_DPS = "3"
HUMIDITY_DPS = "4"
LIGHT_DPS = "101"
CURRENTTEMP_DPS = "103"


class TestElectriqCD20ProDehumidifier(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "electriq_cd12pw_dehumidifier.yaml", ELECTRIQ_CD12PW_DEHUMIDIFIER_PAYLOAD
        )
        self.subject = self.entities.get("humidifier")
        self.light = self.entities.get("light_display")

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_MODES)

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

        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-on")
        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-off")

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

        self.dps[SWITCH_DPS] = False
        self.assertFalse(self.subject.is_on)

        self.dps[SWITCH_DPS] = None
        self.assertIsNone(self.subject.is_on)

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

    def test_mode(self):
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

    async def test_set_mode_to_fan(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "fan",
            },
        ):
            await self.subject.async_set_mode("Air clean")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [COLOR_MODE_ONOFF],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, COLOR_MODE_ONOFF)

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

    def test_state_attributes(self):
        self.dps[CURRENTHUMID_DPS] = 50
        self.dps[CURRENTTEMP_DPS] = 21
        self.assertDictEqual(
            self.subject.device_state_attributes,
            {"current_humidity": 50, "current_temperature": 21},
        )
        self.assertEqual(self.light.device_state_attributes, {})
