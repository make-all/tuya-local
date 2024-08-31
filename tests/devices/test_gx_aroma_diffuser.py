# Test the multi-model config for YYM/GX aroma diffusers - specifically
# the conditional mapping of fan speed to either high/low or large/small.
from ..const import GX_AROMA_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

FANSWITCH_DP = "1"
FANSPEED_DP = "2"
TIMER_DP = "3"
REMAIN_DP = "4"
LIGHTSWITCHDP = "5"
LIGHTMODE_DP = "6"
LIGHTCOLOR_DP = "8"
ERROR_DP = "9"


class TestAromaDiffuser(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("yym_805SW_aroma_nightlight.yaml", GX_AROMA_PAYLOAD)
        self.subject = self.entities["fan_aroma_diffuser"]
        self.mark_secondary(["select_timer"])

    def test_speed_step(self):
        # YYM diffuser
        self.dps[FANSPEED_DP] = "large"
        self.assertEqual(self.subject.percentage_step, 50)
        self.assertEqual(self.subject.speed_count, 2)
        self.dps[FANSPEED_DP] = "small"
        self.assertEqual(self.subject.percentage_step, 50)
        self.assertEqual(self.subject.speed_count, 2)
        # GX diffuser
        self.dps[FANSPEED_DP] = "high"
        self.assertEqual(self.subject.percentage_step, 50)
        self.assertEqual(self.subject.speed_count, 2)
        self.dps[FANSPEED_DP] = "high"
        self.assertEqual(self.subject.percentage_step, 50)
        self.assertEqual(self.subject.speed_count, 2)

    def test_speed(self):
        # YYM diffuser
        self.dps[FANSPEED_DP] = "large"
        self.assertEqual(self.subject.percentage, 100)
        self.dps[FANSPEED_DP] = "small"
        self.assertEqual(self.subject.percentage, 50)
        # GX diffuser
        self.dps[FANSPEED_DP] = "high"
        self.assertEqual(self.subject.percentage, 100)
        self.dps[FANSPEED_DP] = "low"
        self.assertEqual(self.subject.percentage, 50)

    async def test_set_fan_speed_yym(self):
        self.dps[FANSPEED_DP] = "large"
        async with assert_device_properties_set(
            self.subject._device,
            {FANSPEED_DP: "small"},
        ):
            await self.subject.async_set_percentage(50)

    async def test_set_fan_speed_gx(self):
        self.dps[FANSPEED_DP] = "high"
        async with assert_device_properties_set(
            self.subject._device,
            {FANSPEED_DP: "low"},
        ):
            await self.subject.async_set_percentage(50)
