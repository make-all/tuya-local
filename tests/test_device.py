from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from custom_components.goldair_climate.const import (
    CONF_TYPE_DEHUMIDIFIER,
    CONF_TYPE_FAN,
    CONF_TYPE_GECO_HEATER,
    CONF_TYPE_GPCV_HEATER,
    CONF_TYPE_GPPH_HEATER,
)
from custom_components.goldair_climate.device import GoldairTuyaDevice

from .const import (
    DEHUMIDIFIER_PAYLOAD,
    FAN_PAYLOAD,
    GECO_HEATER_PAYLOAD,
    GPCV_HEATER_PAYLOAD,
    GPPH_HEATER_PAYLOAD,
)


class TestDevice(IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch("pytuya.Device")
        self.addCleanup(patcher.stop)
        self.mock_api = patcher.start()
        self.subject = GoldairTuyaDevice(
            "Some name", "some_dev_id", "some.ip.address", "some_local_key", None
        )

    def test_configures_pytuya_correctly(self):
        self.mock_api.assert_called_once_with(
            "some_dev_id", "some.ip.address", "some_local_key", "device"
        )
        self.assertIs(self.subject._api, self.mock_api())

    def test_name(self):
        """Returns the name given at instantiation."""
        self.assertEqual("Some name", self.subject.name)

    def test_unique_id(self):
        """Returns the unique ID presented by the API class."""
        self.assertIs(self.subject.unique_id, self.mock_api().id)

    def test_device_info(self):
        """Returns generic info plus the unique ID for categorisation."""
        self.assertEqual(
            self.subject.device_info,
            {
                "identifiers": {("goldair_climate", self.mock_api().id)},
                "name": "Some name",
                "manufacturer": "Goldair",
            },
        )

    async def test_detects_geco_heater_payload(self):
        self.subject._cached_state = GECO_HEATER_PAYLOAD
        self.assertEqual(
            await self.subject.async_inferred_type(), CONF_TYPE_GECO_HEATER
        )

    async def test_detects_gpcv_heater_payload(self):
        self.subject._cached_state = GPCV_HEATER_PAYLOAD
        self.assertEqual(
            await self.subject.async_inferred_type(), CONF_TYPE_GPCV_HEATER
        )

    async def test_detects_gpph_heater_payload(self):
        self.subject._cached_state = GPPH_HEATER_PAYLOAD
        self.assertEqual(
            await self.subject.async_inferred_type(), CONF_TYPE_GPPH_HEATER
        )

    async def test_detects_dehumidifier_payload(self):
        self.subject._cached_state = DEHUMIDIFIER_PAYLOAD
        self.assertEqual(
            await self.subject.async_inferred_type(), CONF_TYPE_DEHUMIDIFIER
        )

    async def test_detects_fan_payload(self):
        self.subject._cached_state = FAN_PAYLOAD
        self.assertEqual(await self.subject.async_inferred_type(), CONF_TYPE_FAN)
