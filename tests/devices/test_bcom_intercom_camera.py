"""Tests for the bcom intercom camera"""

from ..const import BCOM_CAMERA_PAYLOAD
from .base_device_tests import TuyaDeviceTestCase

LIGHT_DPS = "101"
FLIP_DPS = "103"
WATERMARK_DPS = "104"
MOTION_DPS = "106"
NIGHT_DPS = "108"
SDSIZE_DPS = "109"
SDSTATUS_DPS = "110"
SDFORMAT_DPS = "111"
SNAPSHOT_DPS = "115"
SDFMTSTATE_DPS = "117"
DOORBELL_DPS = "136"
RECORD_DPS = "150"
RECMODE_DPS = "151"
REBOOT_DPS = "162"
CHANNEL_DPS = "231"
LOCK_DPS = "232"


class TestBcomIntercomCamera(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("bcom_intercom_camera.yaml", BCOM_CAMERA_PAYLOAD)
        self.subject = self.entities.get("camera")

        self.mark_secondary(
            [
                "light_indicator",
                "switch_flip_image",
                "switch_watermark",
                "select_motion_detection",
                "select_night_vision",
                "sensor_sd_capacity",
                "sensor_sd_status",
                "button_sd_format",
                "sensor_sd_format_state",
                "select_recording_mode",
                "button_restart",
                "sensor_channel",
            ]
        )

    def test_is_recording(self):
        self.dps[RECORD_DPS] = True
        self.assertTrue(self.subject.is_recording)
        self.dps[RECORD_DPS] = False
        self.assertFalse(self.subject.is_recording)

    def test_motion_detection_enabled(self):
        self.assertIsNone(self.subject.motion_detection_enabled)

    def test_is_on(self):
        self.assertIsNone(self.subject.is_on)

    async def test_camera_image(self):
        self.dps[DOORBELL_DPS] = ""
        self.dps[SNAPSHOT_DPS] = "VGVzdA=="
        image = await self.subject.async_camera_image()
        self.assertEqual(image, b"Test")

        self.dps[DOORBELL_DPS] = "a25vY2sga25vY2s="
        image = await self.subject.async_camera_image()
        self.assertEqual(image, b"knock knock")

    async def test_turn_off(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_turn_off()

    async def test_turn_on(self):
        with self.assertRaises(NotImplementedError):
            await self.subject.async_turn_on()
