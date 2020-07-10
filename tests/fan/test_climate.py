from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_SLEEP,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SWING_HORIZONTAL,
    SWING_OFF,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from custom_components.tuya_local.fan.climate import GoldairFan
from custom_components.tuya_local.fan.const import (
    FAN_MODES,
    HVAC_MODE_TO_DPS_MODE,
    PRESET_MODE_TO_DPS_MODE,
    PRESET_NORMAL,
    PROPERTY_TO_DPS_ID,
    SWING_MODE_TO_DPS_MODE,
)

from ..const import FAN_PAYLOAD
from ..helpers import assert_device_properties_set


class TestGoldairFan(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch(
            "custom_components.tuya_local.device.GoldairTuyaDevice"
        )
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = GoldairFan(self.mock_device())

        self.dps = FAN_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_icon_is_fan(self):
        self.assertEqual(self.subject.icon, "mdi:fan")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_hvac_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_NORMAL)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_ECO
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_ECO)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_SLEEP
        ]
        self.assertEqual(self.subject.preset_mode, PRESET_SLEEP)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertEqual(
            self.subject.preset_modes, [PRESET_NORMAL, PRESET_ECO, PRESET_SLEEP]
        )

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_NORMAL
                ]
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_NORMAL)

    async def test_set_preset_mode_to_eco(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[PRESET_ECO]},
        ):
            await self.subject.async_set_preset_mode(PRESET_ECO)

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]: PRESET_MODE_TO_DPS_MODE[
                    PRESET_SLEEP
                ]
            },
        ):
            await self.subject.async_set_preset_mode(PRESET_SLEEP)

    def test_swing_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]] = SWING_MODE_TO_DPS_MODE[
            SWING_OFF
        ]
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]] = SWING_MODE_TO_DPS_MODE[
            SWING_HORIZONTAL
        ]
        self.assertEqual(self.subject.swing_mode, SWING_HORIZONTAL)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]] = None
        self.assertIs(self.subject.swing_mode, None)

    def test_swing_modes(self):
        self.assertEqual(self.subject.swing_modes, [SWING_OFF, SWING_HORIZONTAL])

    async def test_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]: SWING_MODE_TO_DPS_MODE[SWING_OFF]},
        ):
            await self.subject.async_set_swing_mode(SWING_OFF)

    async def test_set_swing_mode_to_horizontal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]: SWING_MODE_TO_DPS_MODE[
                    SWING_HORIZONTAL
                ]
            },
        ):
            await self.subject.async_set_swing_mode(SWING_HORIZONTAL)

    def test_fan_modes(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]
        self.assertEqual(self.subject.fan_modes, list(range(1, 13)))

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_ECO
        ]
        self.assertEqual(self.subject.fan_modes, [1, 2, 3])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_SLEEP
        ]
        self.assertEqual(self.subject.fan_modes, [1, 2, 3])

        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None
        self.assertEqual(self.subject.fan_modes, [])

    def test_fan_mode_for_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "1"
        self.assertEqual(self.subject.fan_mode, 1)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "6"
        self.assertEqual(self.subject.fan_mode, 6)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "12"
        self.assertEqual(self.subject.fan_mode, 12)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = None
        self.assertEqual(self.subject.fan_mode, None)

    async def test_set_fan_mode_for_normal_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_NORMAL
        ]

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]: "6"},
        ):
            await self.subject.async_set_fan_mode(6)

    def test_fan_mode_for_eco_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_ECO
        ]

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "4"
        self.assertEqual(self.subject.fan_mode, 1)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "8"
        self.assertEqual(self.subject.fan_mode, 2)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "12"
        self.assertEqual(self.subject.fan_mode, 3)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = None
        self.assertEqual(self.subject.fan_mode, None)

    async def test_set_fan_mode_for_eco_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_ECO
        ]

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]: "4"},
        ):
            await self.subject.async_set_fan_mode(1)

    def test_fan_mode_for_sleep_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_SLEEP
        ]

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "4"
        self.assertEqual(self.subject.fan_mode, 1)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "8"
        self.assertEqual(self.subject.fan_mode, 2)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = "12"
        self.assertEqual(self.subject.fan_mode, 3)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]] = None
        self.assertEqual(self.subject.fan_mode, None)

    async def test_set_fan_mode_for_sleep_preset(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = PRESET_MODE_TO_DPS_MODE[
            PRESET_SLEEP
        ]

        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_FAN_MODE]: "8"},
        ):
            await self.subject.async_set_fan_mode(2)

    async def test_set_fan_mode_does_nothing_when_preset_mode_is_not_set(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_PRESET_MODE]] = None

        with self.assertRaises(
            ValueError, msg="Fan mode can only be set when a preset mode is set"
        ):
            await self.subject.async_set_fan_mode(2)

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()
