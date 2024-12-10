"""
Test BLE smart plant sensor.
Primarily for testing the refresh button used in this device, which is
made by sending the temperature unit as the current setting so as to
give the device a command to initiate a data transmission without actually
changing anything.
"""

from ..const import BLE_SMARTPLANT_PAYLOAD
from ..helpers import assert_device_properties_set
from .base_device_tests import TuyaDeviceTestCase

MOISTURE_DP = "3"
TEMPERATURE_DP = "5"
TEMPERATURE_UNIT_DP = "9"
BATTERY_STATE_DP = "14"
BATTERY_DP = "15"


class TestBleSmartPlant(TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig(
            "ble_smart_plant_moisture.yaml",
            BLE_SMARTPLANT_PAYLOAD,
        )
        self.refresh_button = self.entities.get("button_refresh")
        self.mark_secondary(
            [
                "sensor_battery",
                "select_temperature_unit",
                "button_refresh",
            ]
        )

    async def test_refresh_logic(self):
        self.dps[TEMPERATURE_UNIT_DP] = "c"

        async with assert_device_properties_set(
            self.refresh_button._device,
            {TEMPERATURE_UNIT_DP: "c"},
        ):
            await self.refresh_button.async_press()

        self.dps[TEMPERATURE_UNIT_DP] = "f"

        async with assert_device_properties_set(
            self.refresh_button._device,
            {TEMPERATURE_UNIT_DP: "f"},
        ):
            await self.refresh_button.async_press()
