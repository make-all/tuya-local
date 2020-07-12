from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.switch import ATTR_CURRENT_POWER_W, DEVICE_CLASS_OUTLET
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tuya_local.kogan_socket.const import (
    ATTR_SWITCH,
    ATTR_TIMER,
    ATTR_CURRENT_A,
    ATTR_VOLTAGE_V,
    PROPERTY_TO_DPS_ID,
)
from custom_components.tuya_local.kogan_socket.switch import KoganSocketSwitch

from ..const import KOGAN_SOCKET_PAYLOAD
from ..helpers import assert_device_properties_set


class TestKoganSocket(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = KoganSocketSwitch(self.mock_device())

        self.dps = KOGAN_SOCKET_PAYLOAD.copy()
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
        self.assertEqual(self.subject.device_class, DEVICE_CLASS_OUTLET)

    def test_is_on(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWITCH]] = True
        self.assertEqual(self.subject.is_on, True)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWITCH]] = False
        self.assertEqual(self.subject.is_on, False)

    def test_is_on_when_unavailable(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWITCH]] = None
        self.assertEqual(self.subject.is_on, STATE_UNAVAILABLE)

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_SWITCH]: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_SWITCH]: False}
        ):
            await self.subject.async_turn_off()

    async def test_toggle_turns_the_switch_on_when_it_was_off(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWITCH]] = False

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_SWITCH]: True}
        ):
            await self.subject.async_toggle()

    async def test_toggle_turns_the_switch_off_when_it_was_on(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWITCH]] = True
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_SWITCH]: False}
        ):
            await self.subject.async_toggle()

    def test_current_power_w(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_CURRENT_POWER_W]] = 1234
        self.assertEqual(self.subject.current_power_w, 123.4)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_CURRENT_POWER_W]] = None
        self.assertEqual(self.subject.current_power_w, STATE_UNAVAILABLE)

    def test_device_state_attributes_set(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TIMER]] = 1
        self.dps[PROPERTY_TO_DPS_ID[ATTR_VOLTAGE_V]] = 2350
        self.dps[PROPERTY_TO_DPS_ID[ATTR_CURRENT_A]] = 1234
        self.dps[PROPERTY_TO_DPS_ID[ATTR_CURRENT_POWER_W]] = 5678
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                ATTR_TIMER: 1,
                ATTR_CURRENT_A: 1.234,
                ATTR_VOLTAGE_V: 235.0,
                ATTR_CURRENT_POWER_W: 567.8,
            },
        )

        self.dps[PROPERTY_TO_DPS_ID[ATTR_TIMER]] = 0
        self.dps[PROPERTY_TO_DPS_ID[ATTR_VOLTAGE_V]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_CURRENT_A]] = None
        self.dps[PROPERTY_TO_DPS_ID[ATTR_CURRENT_POWER_W]] = None
        self.assertEqual(
            self.subject.device_state_attributes,
            {
                ATTR_TIMER: 0,
                ATTR_CURRENT_A: None,
                ATTR_VOLTAGE_V: None,
                ATTR_CURRENT_POWER_W: STATE_UNAVAILABLE,
            },
        )

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
