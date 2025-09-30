"""Tests for the ELEGRP DTR10 dimmer switch."""

from homeassistant.components.light import ColorMode
from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import PERCENTAGE

from ..const import ELEGRP_DTR10_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import DimmableLightTests
from ..mixins.number import MultiNumberTests
from ..mixins.select import MultiSelectTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
BRIGHTNESS_DPS = "2"
MIN_BRIGHTNESS_DPS = "3"
BULB_TYPE_DPS = "4"
MAX_BRIGHTNESS_DPS = "5"
INDICATOR_BRIGHTNESS_DPS = "101"
FADE_ON_SPEED_DPS = "103"
TIMER_REMAINING_DPS = "6"
FADE_OFF_SPEED_DPS = "104"
LONGPRESS_BRIGHTNESS_DPS = "108"
TIMER_MODE_DPS = "110"
TIMER_DPS = "111"
FIRMWARE_VERSION_DPS = "113"


class TestElegRPDTR10(
    DimmableLightTests,
    MultiNumberTests,
    MultiSelectTests,
    MultiSensorTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("elegrp_dtr10_dimmer_switch.yaml", ELEGRP_DTR10_PAYLOAD)

        # Set up the main light entity
        self.subject = self.entities.get("light")
        self.setUpDimmableLight(
            BRIGHTNESS_DPS,
            self.subject,
            offval=10,
            tests=[(100, 18), (500, 94), (1000, 191)],
        )

        # Set up number entities
        self.setUpMultiNumber(
            [
                {
                    "dps": MIN_BRIGHTNESS_DPS,
                    "name": "number_minimum_brightness",
                    "min": 0,
                    "max": 50,
                    "unit": PERCENTAGE,
                    "scale": 10,
                    "step": 1,
                },
                {
                    "dps": INDICATOR_BRIGHTNESS_DPS,
                    "name": "number_night_indicator_light",
                    "min": 0,
                    "max": 100,
                    "unit": PERCENTAGE,
                },
                {
                    "dps": TIMER_DPS,
                    "name": "number_timer_duration",
                    "min": 0,
                    "max": 86400,
                    "unit": "s",
                },
            ]
        )

        # Set up select entities
        self.setUpMultiSelect(
            [
                {
                    "dps": BULB_TYPE_DPS,
                    "name": "select_bulb_type",
                    "options": {
                        "Cfl": "CFL",
                        "Led": "LED",
                        "Incandescent": "Incandescent",
                        "Halogen": "Halogen",
                    },
                },
                {
                    "dps": FADE_ON_SPEED_DPS,
                    "name": "select_fade_on_speed",
                    "options": {
                        "Immediate": "Immediate",
                        "Fast": "Fast (1s)",
                        "Medium": "Medium (5s)",
                        "Slow": "Slow (15s)",
                    },
                },
                {
                    "dps": FADE_OFF_SPEED_DPS,
                    "name": "select_fade_off_speed",
                    "options": {
                        "Immediate": "Immediate",
                        "Fast": "Fast (1s)",
                        "Medium": "Medium (5s)",
                        "Slow": "Slow (15s)",
                    },
                },
                {
                    "dps": LONGPRESS_BRIGHTNESS_DPS,
                    "name": "select_long_press_on",
                    "options": {
                        1000: "Max Brightness",
                        258: "Nap 25%",
                        505: "Cuddle 50%",
                        753: "Leisure 75%",
                        1000: "Bright 100%",
                    },
                },
                {
                    "dps": TIMER_MODE_DPS,
                    "name": "select_timer_auto_on_mode",
                    "options": {
                        False: "Off",
                        True: "On",
                    },
                },
            ]
        )

        # Set up sensor entities
        self.setUpMultiSensor(
            [
                {
                    "dps": TIMER_REMAINING_DPS,
                    "name": "sensor_timer_remaining",
                    "unit": "s",
                },
                {
                    "dps": FIRMWARE_VERSION_DPS,
                    "name": "sensor_firmware_version",
                },
            ]
        )



                # Mark secondary entities
        self.mark_secondary(
            [
                "number_minimum_brightness",
                "number_night_indicator_light",
                "number_timer_duration",
                "sensor_timer_remaining",
                "sensor_firmware_version",
                "select_bulb_type",
                "select_fade_on_speed",
                "select_fade_off_speed",
                "select_long_press_on",
                "select_timer_auto_on_mode",
            ]
        )

    def test_light_brightness(self):
        """Test the light brightness property."""
        self.dps[BRIGHTNESS_DPS] = 10
        self.assertEqual(self.subject.brightness, 0)

        self.dps[BRIGHTNESS_DPS] = 100
        self.assertEqual(self.subject.brightness, 18)

        self.dps[BRIGHTNESS_DPS] = 500
        self.assertEqual(self.subject.brightness, 94)

        self.dps[BRIGHTNESS_DPS] = 1000
        self.assertEqual(self.subject.brightness, 191)

    def test_light_color_mode(self):
        """Test the light color mode."""
        self.assertEqual(self.subject.color_mode, ColorMode.BRIGHTNESS)

    def test_light_supported_color_modes(self):
        """Test the light supported color modes."""
        self.assertCountEqual(self.subject.supported_color_modes, [ColorMode.BRIGHTNESS])

    async def test_turn_on(self):
        """Test turning on the light."""
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: True}
        ):
            await self.subject.async_turn_on()

    async def test_turn_off(self):
        """Test turning off the light."""
        async with assert_device_properties_set(
            self.subject._device, {SWITCH_DPS: False}
        ):
            await self.subject.async_turn_off()

    async def test_set_brightness(self):
        """Test setting brightness."""
        async with assert_device_properties_set(
            self.subject._device, {BRIGHTNESS_DPS: 100}
        ):
            await self.subject.async_turn_on(brightness=18)

        async with assert_device_properties_set(
            self.subject._device, {BRIGHTNESS_DPS: 500}
        ):
            await self.subject.async_turn_on(brightness=94)

        async with assert_device_properties_set(
            self.subject._device, {BRIGHTNESS_DPS: 1000}
        ):
            await self.subject.async_turn_on(brightness=191)

    def test_extra_state_attributes(self):
        """Test the extra state attributes."""
        self.assertDictEqual(self.subject.extra_state_attributes, {})

    def test_supported_features(self):
        """Test the supported features."""
        self.assertEqual(self.subject.supported_features, 0)
