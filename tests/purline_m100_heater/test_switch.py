from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.switch import DEVICE_CLASS_SWITCH
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.purline_m100_heater.const import (
    ATTR_OPEN_WINDOW_DETECT,
    PROPERTY_TO_DPS_ID,
)
from custom_components.tuya_local.purline_m100_heater.switch import (
    PurlinM100OpenWindowDetector,
)

from ..const import PURLINE_M100_HEATER_PAYLOAD
from ..helpers import assert_device_properties_set


class TestPulineOpenWindowDetector(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = PurlinM100OpenWindowDetector(self.mock_device())

        self.dps = PURLINE_M100_HEATER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_device_class_is_outlet(self):
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_SWITCH)

    def test_is_on(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]] = True
        self.assertEqual(self.subject.is_on, True)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]] = False
        self.assertEqual(self.subject.is_on, False)

    def test_is_on_when_unavailable(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]: False}
        ):
            await self.subject.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]] = False

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]: True}
        ):
            await self.subject.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]] = True
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_OPEN_WINDOW_DETECT]: False}
        ):
            await self.subject.async_toggle()

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
