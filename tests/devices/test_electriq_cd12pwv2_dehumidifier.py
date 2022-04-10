from homeassistant.components.humidifier import SUPPORT_MODES
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
)

from ..const import ELECTRIQ_CD12PWV2_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.light import BasicLightTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
HUMIDITY_DPS = "2"
MODE_DPS = "5"
CURRENTHUMID_DPS = "6"
ERROR_DPS = "19"
LIGHT_DPS = "101"
SLEEP_DPS = "104"


class TestElectriqCD12PWV2Dehumidifier(
    BasicBinarySensorTests,
    BasicLightTests,
    BasicSensorTests,
    BasicSwitchTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "electriq_cd12pwv2_dehumidifier.yaml",
            ELECTRIQ_CD12PWV2_DEHUMIDIFIER_PAYLOAD,
        )
        self.subject = self.entities.get("humidifier")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicBinarySensor(
            ERROR_DPS, self.entities.get("binary_sensor_tank"), testdata=(1, 0)
        )
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_display"))
        self.setUpBasicSensor(
            CURRENTHUMID_DPS,
            self.entities.get("sensor_current_humidity"),
            unit=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            state_class="measurement",
        )
        self.setUpBasicSwitch(
            SLEEP_DPS,
            self.entities.get("switch_sleep"),
        )
        self.mark_secondary(["light_display", "switch_sleep", "binary_sensor_tank"])

    def test_supported_features(self):
        self.assertEqual(self.subject.supported_features, SUPPORT_MODES)

    def test_icon(self):
        """Test that the icon is as expected."""
        self.dps[SWITCH_DPS] = True
        self.dps[MODE_DPS] = "Smart"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")

        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[MODE_DPS] = "Air_purifier"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

        self.dps[SWITCH_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:air-purifier")

        self.dps[LIGHT_DPS] = True
        self.assertEqual(self.basicLight.icon, "mdi:led-on")
        self.dps[LIGHT_DPS] = False
        self.assertEqual(self.basicLight.icon, "mdi:led-off")

        self.dps[SLEEP_DPS] = True
        self.assertEqual(self.basicSwitch.icon, "mdi:sleep")
        self.dps[SLEEP_DPS] = False
        self.assertEqual(self.basicSwitch.icon, "mdi:sleep-off")

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 35)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 55
        self.assertEqual(self.subject.target_humidity, 55)

    async def test_set_target_humidity_rounds_up_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 55},
        ):
            await self.subject.async_set_humidity(53)

    async def test_set_target_humidity_rounds_down_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 50},
        ):
            await self.subject.async_set_humidity(52)

    def test_mode(self):
        self.dps[MODE_DPS] = "Smart"
        self.assertEqual(self.subject.mode, "Smart")
        self.dps[MODE_DPS] = "Air_purifier"
        self.assertEqual(self.subject.mode, "Air Purifier")

    async def test_set_mode_to_smart(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "Smart",
            },
        ):
            await self.subject.async_set_mode("Smart")
            self.subject._device.anticipate_property_value.assert_not_called()

    async def test_set_mode_to_air_purify(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                MODE_DPS: "Air_purifier",
            },
        ):
            await self.subject.async_set_mode("Air Purifier")
            self.subject._device.anticipate_property_value.assert_not_called()

    def test_extra_state_attributes(self):
        self.dps[CURRENTHUMID_DPS] = 50
        self.dps[ERROR_DPS] = 2
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {"current_humidity": 50, "error_code": 2},
        )
