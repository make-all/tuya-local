from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from custom_components.goldair_climate.dehumidifier.const import (
    ATTR_DISPLAY_ON,
    ATTR_HVAC_MODE,
    PROPERTY_TO_DPS_ID,
)
from custom_components.goldair_climate.dehumidifier.light import (
    GoldairDehumidifierLedDisplayLight,
)

from ..const import DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set


class TestLight(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch(
            "custom_components.goldair_climate.dehumidifier.light.GoldairTuyaDevice"
        )
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = GoldairDehumidifierLedDisplayLight(self.mock_device())

        self.dps = DEHUMIDIFIER_PAYLOAD.copy()
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
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]: False}
        ):
            await self.subject.async_turn_off()

    async def test_toggle_takes_no_action_when_dehumidifier_off(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        await self.subject.async_toggle()
        self.subject._device.async_set_property.assert_not_called

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = False

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]: True}
        ):
            await self.subject.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]] = True

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_DISPLAY_ON]: False}
        ):
            await self.subject.async_toggle()

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
