"""Test the config parser"""
import unittest

from warnings import warn

from custom_components.tuya_local.helpers.device_config import (
    available_configs,
    config_for_legacy_use,
    possible_matches,
    TuyaDeviceConfig,
)

from .const import (
    DEHUMIDIFIER_PAYLOAD,
    EUROM_600_HEATER_PAYLOAD,
    FAN_PAYLOAD,
    GARDENPAC_HEATPUMP_PAYLOAD,
    GECO_HEATER_PAYLOAD,
    GPCV_HEATER_PAYLOAD,
    GPPH_HEATER_PAYLOAD,
    GSH_HEATER_PAYLOAD,
    KOGAN_HEATER_PAYLOAD,
    KOGAN_SOCKET_PAYLOAD,
    KOGAN_SOCKET_PAYLOAD2,
    PURLINE_M100_HEATER_PAYLOAD,
    REMORA_HEATPUMP_PAYLOAD,
    BWT_HEATPUMP_PAYLOAD,
    EANONS_HUMIDIFIER_PAYLOAD,
    INKBIRD_THERMOSTAT_PAYLOAD,
    ANKO_FAN_PAYLOAD,
)


class TestDeviceConfig(unittest.TestCase):
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
        cfg = config_for_legacy_use("deta_fan")
        q = cfg.match_quality({**KOGAN_HEATER_PAYLOAD, "updated_at": 0})
        self.assertEqual(q, 0)
        q = cfg.match_quality({**GPPH_HEATER_PAYLOAD})
        self.assertEqual(q, 0)

    def test_entity_find_unknown_dps_fails(self):
        """Test that finding a dps that doesn't exist fails."""
        cfg = config_for_legacy_use("kogan_switch")
        non_existing = cfg.primary_entity.find_dps("missing")
        self.assertIsNone(non_existing)

    async def test_dps_async_set_readonly_value_fails(self):
        """Test that setting a readonly dps fails."""
        mock_device = MagicMock()
        cfg = config_for_legacy_use("kogan_switch")
        voltage = cfg.primary_entity.find_dps("voltage_v")
        with self.assertRaises(TypeError):
            await voltage.async_set_value(mock_device, 230)

    async def test_dps_values_returns_none_with_no_mapping(self):
        """Test that a dps with no mapping returns None as its possible values"""
        cfg = config_for_legacy_use("kogan_switch")
        voltage = cfg.primary_entity.find_dps("voltage_v")
        self.assertIsNone(voltage.values)

    # Test detection of all devices.

    def _test_detect(self, payload, legacy_type, legacy_class):
        """Test that payload is detected as the correct type and class."""
        matched = False
        false_matches = []
        quality = 0
        for cfg in possible_matches(payload):
            self.assertTrue(cfg.matches(payload))
            if cfg.legacy_type == legacy_type:
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
            warn(f"{legacy_type} detected with imperfect quality {quality}%")

        best_q = 0
        for cfg in false_matches:
            q = cfg.match_quality(payload)
            if q > best_q:
                best_q = q

        self.assertGreater(quality, best_q)

        # Ensure the same correct config is returned when looked up by type
        cfg = config_for_legacy_use(legacy_type)
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

    def test_gpph_heater_detection(self):
        """Test that GPPH heater can be detected from its sample payload."""
        self._test_detect(GPPH_HEATER_PAYLOAD, "heater", "GoldairHeater")

    def test_gpcv_heater_detection(self):
        """Test that GPCV heater can be detected from its sample payload."""
        self._test_detect(
            GPCV_HEATER_PAYLOAD,
            "gpcv_heater",
            None,
        )

    def test_eurom_heater_detection(self):
        """Test that Eurom heater can be detected from its sample payload."""
        self._test_detect(
            EUROM_600_HEATER_PAYLOAD,
            "eurom_heater",
            None,
        )

    def test_geco_heater_detection(self):
        """Test that GECO heater can be detected from its sample payload."""
        self._test_detect(
            GECO_HEATER_PAYLOAD,
            "geco_heater",
            None,
        )

    def test_kogan_heater_detection(self):
        """Test that Kogan heater can be detected from its sample payload."""
        self._test_detect(
            KOGAN_HEATER_PAYLOAD,
            "kogan_heater",
            None,
        )

    def test_goldair_dehumidifier_detection(self):
        """Test that Goldair dehumidifier can be detected from its sample payload."""
        self._test_detect(
            DEHUMIDIFIER_PAYLOAD,
            "dehumidifier",
            "GoldairDehumidifier",
        )

    def test_goldair_fan_detection(self):
        """Test that Goldair fan can be detected from its sample payload."""
        self._test_detect(FAN_PAYLOAD, "fan", None)

    def test_kogan_socket_detection(self):
        """Test that 1st gen Kogan Socket can be detected from its sample payload."""
        self._test_detect(
            KOGAN_SOCKET_PAYLOAD,
            "kogan_switch",
            None,
        )

    def test_kogan_socket2_detection(self):
        """Test that 2nd gen Kogan Socket can be detected from its sample payload."""
        self._test_detect(
            KOGAN_SOCKET_PAYLOAD2,
            "kogan_switch",
            None,
        )

    def test_gsh_heater_detection(self):
        """Test that GSH heater can be detected from its sample payload."""
        self._test_detect(
            GSH_HEATER_PAYLOAD,
            "gsh_heater",
            None,
        )

    def test_gardenpac_heatpump_detection(self):
        """Test that GardenPac heatpump can be detected from its sample payload."""
        self._test_detect(
            GARDENPAC_HEATPUMP_PAYLOAD,
            "gardenpac_heatpump",
            None,
        )

    def test_purline_heater_detection(self):
        """Test that Purline heater can be detected from its sample payload."""
        self._test_detect(
            PURLINE_M100_HEATER_PAYLOAD,
            "purline_m100_heater",
            None,
        )

    # Non-legacy devices endup being the same as the tests in test_device.py, so
    # skip them.
