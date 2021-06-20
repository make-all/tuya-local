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
            warn(
                f"{legacy_type} also detectable as {cfg.legacy_type} with quality {q}%"
            )

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
        self._test_detect(FAN_PAYLOAD, "fan", "GoldairFan")

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

    # Non-legacy devices start here.
    def test_remora_heatpump_detection(self):
        """Test that Remora heatpump can be detected from its sample payload."""
        self._test_detect(REMORA_HEATPUMP_PAYLOAD, "remora_heatpump", None)

    def test_eanons_humidifier(self):
        """Test that Eanons humidifier can be detected from its sample payload."""
        self._test_detect(EANONS_HUMIDIFIER_PAYLOAD, "eanons_humidifier", None)

    def test_inkbird_thermostat(self):
        """Test that Inkbird thermostat can be detected from its sample payload."""
        self._test_detect(INKBIRD_THERMOSTAT_PAYLOAD, "inkbird_thermostat", None)

    def test_anko_fan(self):
        """Test that Anko fan can be detected from its sample payload."""
        self._test_detect(ANKO_FAN_PAYLOAD, "anko_fan", None)
