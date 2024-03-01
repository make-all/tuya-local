"""Tests for the Avatto roller blinds controller."""

from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature

from ..const import AVATTO_CURTAIN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DP = "1"
BACKLIGHT_DP = "101"


class TestAvattoCurtainSwitch(BasicLightTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "avatto_curtain_switch.yaml",
            AVATTO_CURTAIN_PAYLOAD,
        )
        self.subject = self.entities.get("cover_curtain")
        self.setUpBasicLight(
            BACKLIGHT_DP,
            self.entities.get("light_backlight"),
        )
        self.mark_secondary(["light_backlight"])

    def test_device_class_is_curtain(self):
        self.assertEqual(self.subject.device_class, CoverDeviceClass.CURTAIN)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
            ),
        )

    def test_is_opening(self):
        self.assertIsNone(self.subject.is_opening)

    def test_is_closing(self):
        self.assertIsNone(self.subject.is_closing)

    def test_is_closed(self):
        self.assertIsNone(self.subject.is_closed)

    async def test_open_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "open"},
        ):
            await self.subject.async_open_cover()

    async def test_close_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "close"},
        ):
            await self.subject.async_close_cover()

    async def test_stop_cover(self):
        async with assert_device_properties_set(
            self.subject._device,
            {COMMAND_DP: "stop"},
        ):
            await self.subject.async_stop_cover()
