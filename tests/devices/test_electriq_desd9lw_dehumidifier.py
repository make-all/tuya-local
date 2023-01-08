from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from ..const import ELECTRIQ_DESD9LW_DEHUMIDIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.light import BasicLightTests
from ..mixins.sensor import BasicSensorTests
from ..mixins.switch import BasicSwitchTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
HUMIDITY_DPS = "2"
FAN_DPS = "4"
HVACMODE_DPS = "5"
CURRENTHUM_DPS = "6"
CURRENTTEMP_DPS = "7"
SWING_DPS = "10"
SWITCH_DPS = "12"
LIGHT_DPS = "15"
TEMPERATURE_DPS = "101"


class TestElectriqDESD9LWDehumidifier(
    BasicLightTests,
    BasicSensorTests,
    BasicSwitchTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "electriq_desd9lw_dehumidifier.yaml",
            ELECTRIQ_DESD9LW_DEHUMIDIFIER_PAYLOAD,
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=16,
            max=30,
        )
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light_uv_sterilization"))
        self.setUpBasicSwitch(SWITCH_DPS, self.entities.get("switch_ionizer"))
        self.setUpBasicSensor(
            CURRENTHUM_DPS,
            self.entities.get("sensor_current_humidity"),
            unit=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            state_class="measurement",
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.SWING_MODE
                | ClimateEntityFeature.TARGET_HUMIDITY
                | ClimateEntityFeature.TARGET_TEMPERATURE
            ),
        )

    def test_icon(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "Auto"
        self.assertEqual(self.subject.icon, "mdi:air-humidifier")
        self.dps[HVACMODE_DPS] = "Dehumidity"
        self.assertEqual(self.subject.icon, "mdi:water")
        self.dps[HVACMODE_DPS] = "Heater"
        self.assertEqual(self.subject.icon, "mdi:fire")
        self.dps[HVACMODE_DPS] = "Fan"
        self.assertEqual(self.subject.icon, "mdi:fan")
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:air-humidifier-off")

    def test_temperature_unit_returns_celsius(self):
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 21
        self.assertEqual(self.subject.current_temperature, 21)

    def test_current_humidity(self):
        self.dps[CURRENTHUM_DPS] = 60
        self.assertEqual(self.subject.current_humidity, 60)

    def test_min_target_humidity(self):
        self.assertEqual(self.subject.min_humidity, 35)

    def test_max_target_humidity(self):
        self.assertEqual(self.subject.max_humidity, 80)

    def test_target_humidity(self):
        self.dps[HUMIDITY_DPS] = 45
        self.assertEqual(self.subject.target_humidity, 45)

    async def test_set_target_humidity_rounds_to_5_percent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 55},
        ):
            await self.subject.async_set_humidity(53)

        async with assert_device_properties_set(
            self.subject._device,
            {HUMIDITY_DPS: 45},
        ):
            await self.subject.async_set_humidity(47)

    def test_hvac_mode(self):
        self.dps[POWER_DPS] = True
        self.dps[HVACMODE_DPS] = "Heater"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

        self.dps[HVACMODE_DPS] = "Dehumidity"
        self.assertEqual(self.subject.hvac_mode, HVACMode.DRY)

        self.dps[HVACMODE_DPS] = "Fan"
        self.assertEqual(self.subject.hvac_mode, HVACMode.FAN_ONLY)

        self.dps[HVACMODE_DPS] = "Auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.AUTO)

        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.AUTO,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
                HVACMode.HEAT,
                HVACMode.OFF,
            ],
        )

    async def test_turn_on(self):
        self.dps[HVACMODE_DPS] = "Auto"
        self.dps[POWER_DPS] = False

        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: True, HVACMODE_DPS: "Heater"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_turn_off(self):
        self.dps[HVACMODE_DPS] = "Auto"
        self.dps[POWER_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {POWER_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    async def test_set_mode_to_heater(self):
        self.dps[HVACMODE_DPS] = "Auto"
        self.dps[POWER_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "Heater", POWER_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_mode_to_dehumidity(self):
        self.dps[HVACMODE_DPS] = "Auto"
        self.dps[POWER_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "Dehumidity", POWER_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.DRY)

    async def test_set_mode_to_fan(self):
        self.dps[HVACMODE_DPS] = "Auto"
        self.dps[POWER_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "Fan", POWER_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.FAN_ONLY)

    async def test_set_mode_to_auto(self):
        self.dps[HVACMODE_DPS] = "Fan"
        self.dps[POWER_DPS] = True

        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "Auto", POWER_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.AUTO)

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "Low"
        self.assertEqual(self.subject.fan_mode, "Low")
        self.dps[FAN_DPS] = "Medium"
        self.assertEqual(self.subject.fan_mode, "Medium")
        self.dps[FAN_DPS] = "High"
        self.assertEqual(self.subject.fan_mode, "High")

    def test_fan_mode_invalid_in_auto_hvac_mode(self):
        self.dps[HVACMODE_DPS] = "Auto"
        self.dps[FAN_DPS] = "Low"
        self.assertIs(self.subject.fan_mode, None)

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            ["Low", "Medium", "High"],
        )

    async def test_set_fan_mode_to_low(self):
        async with assert_device_properties_set(self.subject._device, {FAN_DPS: "Low"}):
            await self.subject.async_set_fan_mode("Low")

    async def test_set_fan_mode_to_medium(self):
        async with assert_device_properties_set(
            self.subject._device, {FAN_DPS: "Medium"}
        ):
            await self.subject.async_set_fan_mode("Medium")

    async def test_set_fan_mode_to_high(self):
        async with assert_device_properties_set(
            self.subject._device, {FAN_DPS: "High"}
        ):
            await self.subject.async_set_fan_mode("High")

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            ["off", "vertical"],
        )

    def test_swing_mode(self):
        self.dps[SWING_DPS] = False
        self.assertEqual(self.subject.swing_mode, "off")

        self.dps[SWING_DPS] = True
        self.assertEqual(self.subject.swing_mode, "vertical")

    async def test_set_swing_mode_to_vertical(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: True},
        ):
            await self.subject.async_set_swing_mode("vertical")

    async def test_set_swing_mode_to_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWING_DPS: False},
        ):
            await self.subject.async_set_swing_mode("off")

    def test_light_icon(self):
        self.assertEqual(self.basicLight.icon, "mdi:solar-power")

    def test_switch_icon(self):
        self.assertEqual(self.basicSwitch.icon, "mdi:creation")
