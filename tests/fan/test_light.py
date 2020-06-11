from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from custom_components.goldair_climate.fan.const import (
    ATTR_DISPLAY_ON,
    ATTR_HVAC_MODE,
    PROPERTY_TO_DPS_ID,
)
from custom_components.goldair_climate.fan.light import GoldairFanLedDisplayLight

from ..const import FAN_PAYLOAD


class TestLight(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch(
            "custom_components.goldair_climate.fan.light.GoldairTuyaDevice"
        )
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = GoldairFanLedDisplayLight(self.mock_device())

        self.dps = FAN_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_icon(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = True
        self.assertEqual(self.subject.icon, "mdi:led-on")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = False
        self.assertEqual(self.subject.icon, "mdi:led-off")

    def test_is_on(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = True
        self.assertEqual(self.subject.is_on, True)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = False
        self.assertEqual(self.subject.is_on, False)

    async def test_turn_on(self):
        result = AsyncMock()
        self.subject._device.async_set_property.return_value = result()

        await self.subject.async_turn_on()

        self.subject._device.async_set_property.assert_called_once_with(
            PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], True
        )
        result.assert_awaited()

    async def test_turn_off(self):
        result = AsyncMock()
        self.subject._device.async_set_property.return_value = result()

        await self.subject.async_turn_off()

        self.subject._device.async_set_property.assert_called_once_with(
            PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], False
        )
        result.assert_awaited()

    async def test_toggle_takes_no_action_when_fan_off(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        await self.subject.async_toggle()
        self.subject._device.async_set_property.assert_not_called

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        result = AsyncMock()
        self.subject._device.async_set_property.return_value = result()
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = False

        await self.subject.async_toggle()

        self.subject._device.async_set_property.assert_called_once_with(
            PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], True
        )
        result.assert_awaited()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        result = AsyncMock()
        self.subject._device.async_set_property.return_value = result()
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = True

        await self.subject.async_toggle()

        self.subject._device.async_set_property.assert_called_once_with(
            PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON], False
        )
        result.assert_awaited()

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
