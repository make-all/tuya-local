"""Test the config parser"""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from custom_components.tuya_local.helpers.config import get_device_id
from custom_components.tuya_local.helpers.device_config import (
    available_configs,
    get_config,
    _bytes_to_fmt,
    _typematch,
    TuyaDeviceConfig,
    TuyaDpsConfig,
    TuyaEntityConfig,
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

    def check_entity(self, entity, cfg):
        """
        Check that the entity has a dps list and each dps has an id,
        type and name.
        """
        self.assertIsNotNone(
            entity._config.get("entity"), f"entity type missing in {cfg}"
        )
        e = entity.config_id
        self.assertIsNotNone(
            entity._config.get("dps"), f"dps missing from {e} in {cfg}"
        )
        for dp in entity.dps():
            self.assertIsNotNone(
                dp._config.get("id"), f"dp id missing from {e} in {cfg}"
            )
            self.assertIsNotNone(
                dp._config.get("type"), f"dp type missing from {e} in {cfg}"
            )
            self.assertIsNotNone(
                dp._config.get("name"), f"dp name missing from {e} in {cfg}"
            )

    def test_config_files_parse(self):
        """
        All configs should be parsable and meet certain criteria
        """
        for cfg in available_configs():
            parsed = TuyaDeviceConfig(cfg)
            # Check for error messages or unparsed config
            if isinstance(parsed, str) or isinstance(parsed._config, str):
                self.fail(f"unparsable yaml in {cfg}")

            self.assertIsNotNone(
                parsed._config.get("name"),
                f"name missing from {cfg}",
            )
            self.assertIsNotNone(
                parsed._config.get("primary_entity"),
                f"primary_entity missing from {cfg}",
            )
            self.check_entity(parsed.primary_entity, cfg)
            for entity in parsed.secondary_entities():
                self.check_entity(entity, cfg)

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
        """
        Test that a dps with no mapping returns None as its possible values
        """
        mock_device = MagicMock()
        cfg = get_config("kogan_switch")
        voltage = cfg.primary_entity.find_dps("voltage_v")
        self.assertIsNone(voltage.values(mock_device))

    def test_config_returned(self):
        """Test that config file is returned by config"""
        cfg = get_config("kogan_switch")
        self.assertEqual(cfg.config, "smartplugv1.yaml")

    def test_float_matches_ints(self):
        """Test that the _typematch function matches int values to float dps"""
        self.assertTrue(_typematch(float, 1))

    def test_bytes_to_fmt_returns_string_for_unknown(self):
        """
        Test that the _bytes_to_fmt function parses unknown number of bytes
        as a string format.
        """
        self.assertEqual(_bytes_to_fmt(5), "5s")

    def test_deprecation(self):
        """Test that deprecation messages are picked from the config."""
        mock_device = MagicMock()
        mock_device.name = "Testing"
        mock_config = {"entity": "Test", "deprecated": "Passed"}
        cfg = TuyaEntityConfig(mock_device, mock_config)
        self.assertTrue(cfg.deprecated)
        self.assertEqual(
            cfg.deprecation_message,
            "The use of Test for Testing is deprecated and should be "
            "replaced by Passed.",
        )

    def test_format_with_none_defined(self):
        """Test that format returns None when there is none configured."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "string"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertIsNone(cfg.format)

    def test_decoding_base64(self):
        """Test that decoded_value works with base64 encoding."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "base64"}
        mock_device = MagicMock()
        mock_device.get_property.return_value = "VGVzdA=="
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(
            cfg.decoded_value(mock_device),
            bytes("Test", "utf-8"),
        )

    def test_decoding_unencoded(self):
        """Test that decoded_value returns the raw value when not encoded."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "string"}
        mock_device = MagicMock()
        mock_device.get_property.return_value = "VGVzdA=="
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(
            cfg.decoded_value(mock_device),
            "VGVzdA==",
        )

    def test_encoding_base64(self):
        """Test that encode_value works with base64."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "base64"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(cfg.encode_value(bytes("Test", "utf-8")), "VGVzdA==")

    def test_encoding_unencoded(self):
        """Test that encode_value works with base64."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "string"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(cfg.encode_value("Test"), "Test")

    def test_match_returns_false_on_errors_with_bitfield(self):
        """Test that TypeError and ValueError cause match to return False."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "bitfield"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertFalse(cfg._match(15, "not an integer"))

    def test_values_with_mirror(self):
        """Test that value_mirror redirects."""
        mock_entity = MagicMock()
        mock_config = {
            "id": "1",
            "type": "string",
            "name": "test",
            "mapping": [
                {"dps_val": "mirror", "value_mirror": "map_mirror"},
                {"dps_val": "plain", "value": "unmirrored"},
            ],
        }
        mock_map_config = {
            "id": "2",
            "type": "string",
            "name": "map_mirror",
            "mapping": [
                {"dps_val": "1", "value": "map_one"},
                {"dps_val": "2", "value": "map_two"},
            ],
        }
        mock_device = MagicMock()
        mock_device.get_property.return_value = "1"
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        map = TuyaDpsConfig(mock_entity, mock_map_config)
        mock_entity.find_dps.return_value = map

        self.assertCountEqual(
            cfg.values(mock_device),
            ["unmirrored", "map_one", "map_two"],
        )

    # values gets very complex, with things like mappings within conditions
    # within mappings. I'd expect something like this was added with purpose,
    # but it isn't exercised by any of the existing unit tests.
    # value-mirror above is explained by the fact that the device it was
    # added for never worked properly, so was removed.

    def test_default_without_mapping(self):
        """Test that default returns None when there is no mapping"""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "string"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertIsNone(cfg.default())

    def test_get_device_id(self):
        """Test that check if device id is correct"""
        self.assertEqual(
            "my-device-id",
            get_device_id({"device_id": "my-device-id"}),
        )
        self.assertEqual("sub-id", get_device_id({"device_cid": "sub-id"}))
        self.assertEqual(
            "s",
            get_device_id({"device_id": "d", "device_cid": "s"}),
        )
