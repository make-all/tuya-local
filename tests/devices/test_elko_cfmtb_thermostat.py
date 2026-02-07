from datetime import datetime, timezone

from ..const import ELKO_CFMTB_THERMOSTAT_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

OVERRIDE_END_DPS = "108"


class TestElkoCFMTBThermostat(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "elko_cfmtb_thermostat.yaml",
            ELKO_CFMTB_THERMOSTAT_PAYLOAD,
        )
        self.subject = self.entities.get("datetime_override_end")
        self.mark_secondary(
            [
                "number_power_rating",
                "lock_child_lock",
                "number_active_screen_brightness",
                "number_standby_screen_brightness",
                "sensor_external_sensor_type",
                "sensor_device_type",
                "sensor_floor_temperature",
                "sensor_air_temperature",
                "sensor_power",
                "sensor_energy",
                "datetime_override_end",
                "number_heating_temperature",
                "number_cooling_temperature",
                "number_away_heating_reduction",
                "number_away_cooling_reduction",
                "number_away_minimum_temperature",
                "number_away_maximum_temperature",
                "switch_away",
                "switch_schedule",
                "binary_sensor_occupancy",
                "binary_sensor_window",
                "number_room_temperature_calibration",
                "number_external_temperature_calibration",
                "number_screen_timeout",
                "switch_screen_timeout",
                "switch_regulator_mode",
            ]
        )

    def test_datetime_override_end(self):
        self.dps[OVERRIDE_END_DPS] = (
            1770465243 - datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()
        )
        self.assertEqual(
            self.subject.native_value,
            datetime(2026, 2, 7, 11, 54, 3, tzinfo=timezone.utc),
        )

    async def test_set_datetime_override_end(self):
        MILLINIUM = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()
        async with assert_device_properties_set(
            self.subject._device,
            {OVERRIDE_END_DPS: 1770465243 - MILLINIUM},
        ):
            await self.subject.async_set_value(
                datetime(2026, 2, 7, 11, 54, 3, tzinfo=timezone.utc)
            )
