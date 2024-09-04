"""Tests for the tilt position feature of AM25 roller blind."""

from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature

from ..const import AM25_ROLLERBLIND_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

COMMAND_DPS = "1"
POSITION_DPS = "2"
CURRENTPOS_DPS = "3"
WORKSTATE_DP = "7"
FAULT_DP = "12"
DIRECTION_DP = "103"
LIMITUP_DP = "104"
LIMITDOWN_DP = "105"
LIMITRESET_DP = "107"
TILTPOS_DP = "109"


class TestAM25Blinds(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "zemismart_am25_rollerblind.yaml",
            AM25_ROLLERBLIND_PAYLOAD,
        )
        self.subject = self.entities["cover_blind"]
        self.mark_secondary(
            [
                "binary_sensor_problem",
                "select_direction",
                "switch_limit_up",
                "switch_limit_down",
                "button_reset_limits",
            ]
        )

    def test_device_class_is_blind(self):
        self.assertEqual(self.subject.device_class, CoverDeviceClass.BLIND)

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.SET_POSITION
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_TILT_POSITION
            ),
        )

    def test_current_cover_tilt_position(self):
        self.dps[TILTPOS_DP] = 1
        self.assertEqual(self.subject.current_cover_tilt_position, 10)

    async def test_set_cover_tilt_position(self):
        async with assert_device_properties_set(
            self.subject._device,
            {TILTPOS_DP: 5},
        ):
            await self.subject.async_set_cover_tilt_position(50)
