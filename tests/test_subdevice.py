import tinytuya

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from custom_components.tuya_local.device import TuyaLocalDevice


class TestSubDevice(IsolatedAsyncioTestCase):

    def setUp(self):
        device_patcher = patch("tinytuya.Device")
        self.addCleanup(device_patcher.stop)
        self.mock_api = device_patcher.start()

        hass_patcher = patch("homeassistant.core.HomeAssistant")
        self.addCleanup(hass_patcher.stop)
        self.hass = hass_patcher.start()

        self.subject = TuyaLocalDevice(
            "Some name", "some_dev_id", "some.ip.address", "some_local_key",
            "some_dev_cid", self.hass()
        )

    def test_configures_tinytuya_correctly(self):
        self.mock_api.assert_called_once_with(
            "some_dev_id", "some.ip.address", "some_local_key", "some_dev_cid"
        )
        self.assertIs(self.subject._api, self.mock_api())

    def test_name(self):
        """Returns the name given at instantiation."""
        self.assertEqual(self.subject.name, "Some name")
