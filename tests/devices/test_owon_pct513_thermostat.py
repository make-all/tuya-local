from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from homeassistant.const import UnitOfTemperature

from ..const import OWON_PCT513_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.climate import TargetTemperatureTests
from ..mixins.number import BasicNumberTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "2"
TEMPERATURE_DPS = "16"
TEMPF_DPS = "17"
UNIT_DPS = "23"
CURRENTTEMP_DPS = "24"
CURRTEMPF_DPS = "29"
CURRENTHUMID_DPS = "34"
UNKNOWN45_DPS = "45"
INSTALL_DPS = "107"
TEMPC_DPS = "108"
UNKNOWN109_DPS = "109"
TEMPF2_DPS = "110"
UNKNOWN111_DPS = "111"
FAN_DPS = "115"
UNKNOWN116_DPS = "116"
SCHED_DPS = "119"
PRESET_DPS = "120"
DUTYCYCLE_DPS = "123"
HVACACTION_DPS = "129"


class TestOwonPCT513Thermostat(
    BasicNumberTests,
    TargetTemperatureTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "owon_pct513_thermostat.yaml", OWON_PCT513_THERMOSTAT_PAYLOAD
        )
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=15.0,
            max=45.0,
            scale=100,
            step=50,
        )
        self.setUpBasicNumber(
            DUTYCYCLE_DPS,
            self.entities.get("number_fan_runtime"),
            max=55,
            step=5,
            unit="min",
        )

        self.mark_secondary(["number_fan_runtime"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            (
                ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TARGET_TEMPERATURE
            ),
        )

    def test_temperature_unit(self):
        self.dps[UNIT_DPS] = "c"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.CELSIUS)
        self.dps[UNIT_DPS] = "f"
        self.assertEqual(self.subject.temperature_unit, UnitOfTemperature.FAHRENHEIT)

    def test_current_temperature(self):
        self.dps[UNIT_DPS] = "c"
        self.dps[CURRENTTEMP_DPS] = 2100
        self.assertEqual(self.subject.current_temperature, 21.00)
        self.dps[UNIT_DPS] = "f"
        self.dps[CURRTEMPF_DPS] = 82
        self.assertEqual(self.subject.current_temperature, 82)

    def test_current_humidity(self):
        self.dps[CURRENTHUMID_DPS] = 50
        self.assertEqual(self.subject.current_humidity, 50)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes,
            [
                HVACMode.COOL,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.OFF,
            ],
        )

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = "off"
        self.assertEqual(self.subject.hvac_mode, HVACMode.OFF)
        self.dps[HVACMODE_DPS] = "cool"
        self.assertEqual(self.subject.hvac_mode, HVACMode.COOL)
        self.dps[HVACMODE_DPS] = "heat"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)
        self.dps[HVACMODE_DPS] = "auto"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT_COOL)
        self.dps[HVACMODE_DPS] = "emergencyheat"
        self.assertEqual(self.subject.hvac_mode, HVACMode.HEAT)

    async def test_set_hvac_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "off"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.OFF)

    async def test_set_hvac_mode_cool(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "cool"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.COOL)

    async def test_set_hvac_mode_heat(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "heat"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT)

    async def test_set_hvac_mode_heatcool(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "auto"}
        ):
            await self.subject.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "off"}
        ):
            await self.subject.async_turn_off()

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: "auto"}
        ):
            await self.subject.async_turn_on()

    def test_hvac_action(self):
        self.dps[HVACACTION_DPS] = "coolfanon"
        self.assertEqual(self.subject.hvac_action, HVACAction.COOLING)
        self.dps[HVACACTION_DPS] = "alloff"
        self.assertEqual(self.subject.hvac_action, HVACAction.IDLE)
        self.dps[HVACACTION_DPS] = "fanon"
        self.assertEqual(self.subject.hvac_action, HVACAction.FAN)
        self.dps[HVACACTION_DPS] = "heatfanon"
        self.assertEqual(self.subject.hvac_action, HVACAction.HEATING)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Manual", "Follow Schedule", "Temporary Hold", "Permanent Hold"],
        )

    def test_preset_mode(self):
        self.dps[SCHED_DPS] = True
        self.dps[PRESET_DPS] = "followschedule"
        self.assertEqual(self.subject.preset_mode, "Follow Schedule")
        self.dps[PRESET_DPS] = "temphold"
        self.assertEqual(self.subject.preset_mode, "Temporary Hold")
        self.dps[PRESET_DPS] = "permhold"
        self.assertEqual(self.subject.preset_mode, "Permanent Hold")
        self.dps[SCHED_DPS] = False
        self.assertEqual(self.subject.preset_mode, "Manual")

    async def test_set_preset_to_schedule(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SCHED_DPS: True,
                PRESET_DPS: "followschedule",
            },
        ):
            await self.subject.async_set_preset_mode("Follow Schedule")

    async def test_set_preset_to_temp_hold(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SCHED_DPS: True,
                PRESET_DPS: "temphold",
            },
        ):
            await self.subject.async_set_preset_mode("Temporary Hold")

    async def test_set_preset_to_perm_hold(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SCHED_DPS: True,
                PRESET_DPS: "permhold",
            },
        ):
            await self.subject.async_set_preset_mode("Permanent Hold")

    async def test_set_preset_to_manual(self):
        async with assert_device_properties_set(
            self.subject._device,
            {
                SCHED_DPS: False,
            },
        ):
            await self.subject.async_set_preset_mode("Manual")

    def test_fan_modes(self):
        self.assertCountEqual(
            self.subject.fan_modes,
            ["on", "auto", "cycle"],
        )

    def test_fan_mode(self):
        self.dps[FAN_DPS] = "on"
        self.assertEqual(self.subject.fan_mode, "on")
        self.dps[FAN_DPS] = "auto"
        self.assertEqual(self.subject.fan_mode, "auto")
        self.dps[FAN_DPS] = "cycle"
        self.assertEqual(self.subject.fan_mode, "cycle")

    async def test_set_fan_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "on"},
        ):
            await self.subject.async_set_fan_mode("on")

    async def test_set_fan_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "auto"},
        ):
            await self.subject.async_set_fan_mode("auto")

    async def test_set_fan_cycle(self):
        async with assert_device_properties_set(
            self.subject._device,
            {FAN_DPS: "cycle"},
        ):
            await self.subject.async_set_fan_mode("cycle")

    def test_extra_state_attributes(self):
        self.dps[UNKNOWN45_DPS] = 45
        self.dps[INSTALL_DPS] = "107"
        self.dps[TEMPC_DPS] = 1080
        self.dps[UNKNOWN109_DPS] = 109
        self.dps[TEMPF2_DPS] = 110
        self.dps[UNKNOWN111_DPS] = 111
        self.dps[UNKNOWN116_DPS] = "116"
        self.assertDictEqual(
            self.subject.extra_state_attributes,
            {
                "unknown_45": 45,
                "installation": "107",
                "temp_c": 10.8,
                "unknown_109": 109,
                "temp_f2": 110,
                "unknown_111": 111,
                "unknown_116": "116",
            },
        )
