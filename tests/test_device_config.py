"""Test the config parser"""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from custom_components.tuya_local.helpers.device_config import (
    available_configs,
    get_config,
    TuyaDeviceConfig,
)

from .const import (
    GPPH_HEATER_PAYLOAD,
    KOGAN_HEATER_PAYLOAD,
)


class TestDeviceConfig(IsolatedAsyncioTestCase):
    """Test the device config parser"""

    def test_can_find_config_files(self):
        """Test that the config files can be found by the parser."""
        found = False
        for cfg in available_configs():
            found = True
            break
        self.assertTrue(found)

    def test_config_files_parse(self):
        for cfg in available_configs():
            parsed = TuyaDeviceConfig(cfg)
            self.assertIsNotNone(parsed.name)

    def test_config_files_have_legacy_link(self):
        """
        Initially, we require a link between the new style config, and the old
        classes so we can transition over to the new config.  When the
        transition is complete, we will drop the requirement, as new devices
        will only be added as config files.
        """
        for cfg in available_configs():
            parsed = TuyaDeviceConfig(cfg)
            self.assertIsNotNone(parsed.legacy_type)
            self.assertIsNotNone(parsed.primary_entity)

    # Most of the device_config functionality is exercised during testing of
    # the various supported devices.  These tests concentrate only on the gaps.

    def test_match_quality(self):
        """Test the match_quality function."""
        cfg = get_config("deta_fan")
        q = cfg.match_quality({**KOGAN_HEATER_PAYLOAD, "updated_at": 0})
        self.assertEqual(q, 0)
        q = cfg.match_quality({**GPPH_HEATER_PAYLOAD})
        self.assertEqual(q, 0)

    def test_entity_find_unknown_dps_fails(self):
        """Test that finding a dps that doesn't exist fails."""
        cfg = get_config("kogan_switch")
        non_existing = cfg.primary_entity.find_dps("missing")
        self.assertIsNone(non_existing)

    async def test_dps_async_set_readonly_value_fails(self):
        """Test that setting a readonly dps fails."""
        mock_device = MagicMock()
        cfg = get_config("kogan_switch")
        voltage = cfg.primary_entity.find_dps("voltage_v")
        with self.assertRaises(TypeError):
            await voltage.async_set_value(mock_device, 230)

    def test_dps_values_returns_none_with_no_mapping(self):
        """Test that a dps with no mapping returns None as its possible values"""
        mock_device = MagicMock()
        cfg = get_config("kogan_switch")
        voltage = cfg.primary_entity.find_dps("voltage_v")
        self.assertIsNone(voltage.values(mock_device))

    def test_config_returned(self):
        """Test that config file is returned by config"""
        cfg = get_config("kogan_switch")
        self.assertEqual(cfg.config, "smartplugv1.yaml")
