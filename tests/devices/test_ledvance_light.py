"""Tests for Ledvance Panel lighting, in particular the combined settings"""

from ..const import LEDVANCE_PANEL_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

POWER_DP = "20"
COMBO_DP = "51"


class TestLedvanceLight(TuyaDeviceTestCase):
    """
    Tests for Ledvance Panel lighting.
    """

    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "ledvance_smart_plabl100x25b.yaml",
            LEDVANCE_PANEL_PAYLOAD,
        )
        self.white = self.entities.get("light")
        self.color = self.entities.get("light_backlight")

        self.mark_secondary(["number_timer"])

    async def test_color_combined_bright(self):
        self.dps[COMBO_DP] = "AAcAOQPoA+gCngDI"
        self.assertEqual(self.color.brightness, 255)
        self.assertEqual(self.white.brightness, 171)
        async with assert_device_properties_set(
            self.white._device,
            {COMBO_DP: "AAcAOQPoA+gD6ADI"},
        ):
            await self.white.async_turn_on(brightness=255)

    async def test_color_combined_rgb(self):
        self.dps[COMBO_DP] = "AAcAOQPoA+gCngDI"
        self.assertSequenceEqual(self.color.hs_color, (57, 100))

        async with assert_device_properties_set(
            self.color._device,
            {COMBO_DP: "AAcAtAPoA+gCngDI"},
        ):
            await self.color.async_turn_on(hs_color=(180, 100))
