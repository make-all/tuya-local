"""Tests for the light entity."""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from custom_components.tuya_local.const import (
    CONF_DISPLAY_LIGHT,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_TYPE_AUTO,
    CONF_TYPE_GPPH_HEATER,
    DOMAIN,
)
from custom_components.tuya_local.generic.light import TuyaLocalLight
from custom_components.tuya_local.helpers.device_config import config_for_legacy_use
from custom_components.tuya_local.light import async_setup_entry

from .const import GPPH_HEATER_PAYLOAD
from .helpers import assert_device_properties_set

GPPH_LIGHTSWITCH_DPS = "104"


async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TYPE: CONF_TYPE_AUTO, CONF_DEVICE_ID: "dummy"},
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()
    m_device.async_inferred_type = AsyncMock(return_value=CONF_TYPE_GPPH_HEATER)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"][CONF_DISPLAY_LIGHT]) == TuyaLocalLight
    m_add_entities.assert_called_once()


class TestTuyaLocalLight(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()
        gpph_config = config_for_legacy_use(CONF_TYPE_GPPH_HEATER)
        for light in gpph_config.secondary_entities():
            if light.entity == "light":
                break
        self.subject = TuyaLocalLight(self.mock_device(), light)
        self.dps = GPPH_HEATER_PAYLOAD.copy()
        self.light_name = light.name
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_friendly_name_returns_config_name(self):
        self.assertEqual(self.subject.friendly_name, self.light_name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_icon(self):
        self.dps[GPPH_LIGHTSWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:led-on")

        self.dps[GPPH_LIGHTSWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:led-off")

    def test_is_on(self):
        self.dps[GPPH_LIGHTSWITCH_DPS] = True
        self.assertEqual(self.subject.is_on, True)

        self.dps[GPPH_LIGHTSWITCH_DPS] = False
        self.assertEqual(self.subject.is_on, False)

    def test_state_attributes(self):
        self.assertEqual(self.subject.device_state_attributes, {})

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {GPPH_LIGHTSWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {GPPH_LIGHTSWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    #    async def test_toggle_takes_no_action_when_heater_off(self):
    #        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
    #        await self.subject.async_toggle()
    #        self.subject._device.async_set_property.assert_not_called

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        #        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[GPPH_LIGHTSWITCH_DPS] = False

        async with assert_device_properties_set(
            self.subject._device, {GPPH_LIGHTSWITCH_DPS: True}
        ):
            await self.subject.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        #        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[GPPH_LIGHTSWITCH_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {GPPH_LIGHTSWITCH_DPS: False}
        ):
            await self.subject.async_toggle()

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
