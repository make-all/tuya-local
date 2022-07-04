from unittest.mock import ANY

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.light import ColorMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import TEMP_CELSIUS, TIME_HOURS

from ..const import DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import MultiBinarySensorTests
from ..mixins.lock import BasicLockTests
from ..mixins.number import BasicNumberTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
PRESET_DPS = "2"
HUMIDITY_DPS = "4"
AIRCLEAN_DPS = "5"
FANMODE_DPS = "6"
LOCK_DPS = "7"
ERROR_DPS = "11"
TIMER_DPS = "12"
UNKNOWN101_DPS = "101"
LIGHTOFF_DPS = "102"
CURRENTTEMP_DPS = "103"
CURRENTHUMID_DPS = "104"
DEFROST_DPS = "105"

PRESET_NORMAL = "0"
PRESET_LOW = "1"
PRESET_HIGH = "2"
PRESET_DRY_CLOTHES = "3"

ERROR_TANK = "Tank full or missing"


class TestGoldairDehumidifier(
    BasicLockTests,
    BasicNumberTests,
    BasicSwitchTests,
    MultiBinarySensorTests,
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("goldair_dehumidifier.yaml", DEHUMIDIFIER_PAYLOAD)
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(HVACMODE_DPS, self.subject)
        self.fan = self.entities.get("fan")
        # BasicLightTests mixin is not used here because the switch is inverted
        self.light = self.entities.get("light_display")
        self.setUpBasicLock(LOCK_DPS, self.entities.get("lock_child_lock"))
        self.setUpBasicSwitch(AIRCLEAN_DPS, self.entities.get("switch_air_clean"))
        self.setUpBasicNumber(
            TIMER_DPS,
            self.entities.get("number_timer"),
            max=24,
            unit=TIME_HOURS,
        )

        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_current_temperature",
                    "dps": CURRENTTEMP_DPS,
                    "unit": TEMP_CELSIUS,
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": "measurement",
                },
                {
                    "name": "sensor_current_humidity",
                    "dps": CURRENTHUMID_DPS,
                    "unit": "%",
                    "device_class": SensorDeviceClass.HUMIDITY,
                    "state_class": "measurement",
                },
            ]
        )
        self.setUpMultiBinarySensors(
            [
                {
                    "name": "binary_sensor_tank",
                    "dps": ERROR_DPS,
                    "device_class": BinarySensorDeviceClass.PROBLEM,
                    "testdata": (8, 0),
                },
                {
                    "name": "binary_sensor_defrost",
                    "dps": DEFROST_DPS,
                    "device_class": BinarySensorDeviceClass.COLD,
                },
            ]
        )
        self.mark_secondary(
            [
                "light_display",
                "lock_child_lock",
                "number_timer",
                "binary_sensor_tank",
                "binary_sensor_defrost",
            ],
        )

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 30)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity_in_humidifier(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.dps[HUMIDITY_DPS] = 45

        self.assertEqual(self.subject.target_humidity, 45)

    async def test_set_humidity_in_humidifier_rounds_up_to_5_percent(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 45},
        ):
            await self.subject.async_set_humidity(43)

    async def test_set_humidity_in_humidifier_rounds_down_to_5_percent(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 40},
        ):
            await self.subject.async_set_humidity(42)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.assertEqual(self.subject.mode, "Normal")

        self.dps[PRESET_DPS] = PRESET_LOW
        self.assertEqual(self.subject.mode, "Low")

        self.dps[PRESET_DPS] = PRESET_HIGH
        self.assertEqual(self.subject.mode, "High")

        self.dps[PRESET_DPS] = PRESET_DRY_CLOTHES
        self.assertEqual(self.subject.mode, "Dry clothes")

        self.dps[PRESET_DPS] = None
        self.assertEqual(self.subject.mode, None)

    def test_fan_mode_reflects_dps_mode_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        self.dps[FANMODE_DPS] = "1"
        self.assertEqual(self.fan.percentage, 50)

        self.dps[FANMODE_DPS] = "3"
        self.assertEqual(self.fan.percentage, 100)

        self.dps[FANMODE_DPS] = None
        self.assertEqual(self.fan.percentage, None)

    async def test_set_fan_50_succeeds_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "1"},
        ):
            await self.fan.async_set_percentage(50)

    async def test_set_fan_100_succeeds_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "3"},
        ):
            await self.fan.async_set_percentage(100)

    async def test_set_fan_30_snaps_to_50_in_normal_preset(self):
        self.dps[PRESET_DPS] = PRESET_NORMAL
        async with assert_device_properties_set(
            self.fan._device,
            {FANMODE_DPS: "1"},
        ):
            await self.fan.async_set_percentage(30)

    def test_light_supported_color_modes(self):
        self.assertCountEqual(
            self.light.supported_color_modes,
            [ColorMode.ONOFF],
        )

    def test_light_color_mode(self):
        self.assertEqual(self.light.color_mode, ColorMode.ONOFF)

    def test_light_icon(self):
        self.dps[LIGHTOFF_DPS] = False
        self.assertEqual(self.light.icon, "mdi:led-on")

        self.dps[LIGHTOFF_DPS] = True
        self.assertEqual(self.light.icon, "mdi:led-off")

    def test_light_is_on(self):
        self.dps[LIGHTOFF_DPS] = False
        self.assertEqual(self.light.is_on, True)

        self.dps[LIGHTOFF_DPS] = True
        self.assertEqual(self.light.is_on, False)

    def test_light_state_attributes(self):
        self.assertEqual(self.light.extra_state_attributes, {})

    async def test_light_turn_on(self):
        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: False}
        ):
            await self.light.async_turn_on()

    async def test_light_turn_off(self):
        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: True}
        ):
            await self.light.async_turn_off()

    async def test_toggle_turns_the_light_on_when_it_was_off(self):
        self.dps[LIGHTOFF_DPS] = True

        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: False}
        ):
            await self.light.async_toggle()

    async def test_toggle_turns_the_light_off_when_it_was_on(self):
        self.dps[LIGHTOFF_DPS] = False

        async with assert_device_properties_set(
            self.light._device, {LIGHTOFF_DPS: True}
        ):
            await self.light.async_toggle()

    def test_switch_icon(self):
        self.assertEqual(self.basicSwitch.icon, "mdi:air-purifier")
