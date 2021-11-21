"""Test the config parser"""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from warnings import warn

from custom_components.tuya_local.helpers.device_config import (
    available_configs,
    get_config,
    possible_matches,
    TuyaDeviceConfig,
)

from .const import (
    DEHUMIDIFIER_PAYLOAD,
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

    # Test detection of all devices.

    def _test_detect(self, payload, dev_type, legacy_class):
        """Test that payload is detected as the correct type and class."""
        matched = False
        false_matches = []
        quality = 0
        for cfg in possible_matches(payload):
            self.assertTrue(cfg.matches(payload))
            if cfg.legacy_type == dev_type:
                self.assertFalse(matched)
                matched = True
                quality = cfg.match_quality(payload)
                if legacy_class is not None:
                    cfg_class = cfg.primary_entity.legacy_class
                    if cfg_class is None:
                        for e in cfg.secondary_entities():
                            cfg_class = e.legacy_class
                            if cfg_class is not None:
                                break

                    self.assertEqual(
                        cfg_class.__name__,
                        legacy_class,
                    )
            else:
                false_matches.append(cfg)

        self.assertTrue(matched)
        if quality < 100:
            warn(f"{dev_type} detected with imperfect quality {quality}%")

        best_q = 0
        for cfg in false_matches:
            q = cfg.match_quality(payload)
            if q > best_q:
                best_q = q

        self.assertGreater(quality, best_q)

        # Ensure the same correct config is returned when looked up by type
        cfg = get_config(dev_type)
        if legacy_class is not None:
            cfg_class = cfg.primary_entity.legacy_class
            if cfg_class is None:
                for e in cfg.secondary_entities():
                    cfg_class = e.legacy_class
                    if cfg_class is not None:
                        break
            self.assertEqual(
                cfg_class.__name__,
                legacy_class,
            )

    def test_goldair_dehumidifier_detection(self):
        """Test that Goldair dehumidifier can be detected from its sample payload."""
        self._test_detect(
            DEHUMIDIFIER_PAYLOAD,
            "dehumidifier",
            "GoldairDehumidifier",
        )

    # Non-legacy devices endup being the same as the tests in test_device.py, so
    # skip them.
