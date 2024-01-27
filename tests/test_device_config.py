"""Test the config parser"""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from fuzzywuzzy import fuzz
from homeassistant.components.sensor import SensorDeviceClass

from custom_components.tuya_local.helpers.config import get_device_id
from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    TuyaDpsConfig,
    TuyaEntityConfig,
    _bytes_to_fmt,
    _typematch,
    available_configs,
    get_config,
)
from custom_components.tuya_local.sensor import TuyaLocalSensor

from .const import GPPH_HEATER_PAYLOAD, KOGAN_HEATER_PAYLOAD

KNOWN_DPS = {
    "alarm_control_panel": {
        "required": ["alarm_state"],
        "optional": ["trigger"],
    },
    "binary_sensor": {"required": ["sensor"], "optional": []},
    "button": {"required": ["button"], "optional": []},
    "camera": {
        "required": [],
        "optional": ["switch", "motion_enable", "snapshot", "record"],
    },
    "climate": {
        "required": [],
        "optional": [
            "aux_heat",
            "current_temperature",
            "current_humidity",
            "fan_mode",
            "humidity",
            "hvac_mode",
            "hvac_action",
            "min_temperature",
            "max_temperature",
            "preset_mode",
            "swing_mode",
            {
                "xor": [
                    "temperature",
                    {"and": ["target_temp_high", "target_temp_low"]},
                ]
            },
            "temperature_unit",
        ],
    },
    "cover": {
        "required": [{"or": ["control", "position"]}],
        "optional": [
            "current_position",
            "action",
            "open",
            "reversed",
        ],
    },
    "event": {"required": ["event"], "optional": []},
    "fan": {
        "required": [{"or": ["preset_mode", "speed"]}],
        "optional": ["switch", "oscillate", "direction"],
    },
    "humidifier": {
        "required": ["humidity"],
        "optional": ["switch", "mode", "current_humidity"],
    },
    "lawn_mower": {"required": ["activity", "command"], "optional": []},
    "light": {
        "required": [{"or": ["switch", "brightness", "effect"]}],
        "optional": ["color_mode", "color_temp", "rgbhsv"],
    },
    "lock": {
        "required": [],
        "optional": [
            "lock",
            {"and": ["request_unlock", "approve_unlock"]},
            {"and": ["request_intercom", "approve_intercom"]},
            "unlock_fingerprint",
            "unlock_password",
            "unlock_temp_pwd",
            "unlock_dynamic_pwd",
            "unlock_offline_pwd",
            "unlock_card",
            "unlock_app",
            "unlock_key",
            "unlock_ble",
            "jammed",
        ],
    },
    "number": {
        "required": ["value"],
        "optional": ["unit", "minimum", "maximum"],
    },
    "remote": {
        "required": ["send"],
        "optional": ["receive"],
    },
    "select": {"required": ["option"], "optional": []},
    "sensor": {"required": ["sensor"], "optional": ["unit"]},
    "siren": {
        "required": [],
        "optional": ["tone", "volume", "duration", "switch"],
    },
    "switch": {"required": ["switch"], "optional": ["current_power_w"]},
    "vacuum": {
        "required": ["status"],
        "optional": [
            "command",
            "locate",
            "power",
            "activate",
            "battery",
            "direction_control",
            "error",
            "fan_speed",
        ],
    },
    "water_heater": {
        "required": [],
        "optional": [
            "current_temperature",
            "operation_mode",
            "temperature",
            "temperature_unit",
            "min_temperature",
            "max_temperature",
            "away_mode",
        ],
    },
}


class TestDeviceConfig(IsolatedAsyncioTestCase):
    """Test the device config parser"""

    def test_can_find_config_files(self):
        """Test that the config files can be found by the parser."""
        found = False
        for cfg in available_configs():
            found = True
            break
        self.assertTrue(found)

    def dp_match(self, condition, accounted, unaccounted, known, required=False):
        if type(condition) is str:
            known.add(condition)
            if condition in unaccounted:
                unaccounted.remove(condition)
                accounted.add(condition)
            if required:
                return condition in accounted
            else:
                return True
        elif "and" in condition:
            return self.and_match(
                condition["and"], accounted, unaccounted, known, required
            )
        elif "or" in condition:
            return self.or_match(condition["or"], accounted, unaccounted, known)
        elif "xor" in condition:
            return self.xor_match(
                condition["xor"], accounted, unaccounted, known, required
            )
        else:
            self.fail(f"Unrecognized condition {condition}")

    def and_match(self, conditions, accounted, unaccounted, known, required):
        single_match = False
        all_match = True
        for cond in conditions:
            match = self.dp_match(cond, accounted, unaccounted, known, True)
            all_match = all_match and match
            single_match = single_match or match
        if required:
            return all_match
        else:
            return all_match == single_match

    def or_match(self, conditions, accounted, unaccounted, known):
        match = False
        # loop through all, to ensure they are transferred to accounted list
        for cond in conditions:
            match = match or self.dp_match(cond, accounted, unaccounted, known, True)
        return match

    def xor_match(self, conditions, accounted, unaccounted, known, required):
        prior_match = False
        for cond in conditions:
            match = self.dp_match(cond, accounted, unaccounted, known, True)

            if match and prior_match:
                return False
            prior_match = prior_match or match

        # If any matched, all should be considered matched
        # this bit only handles nesting "and" within "xor"

        if prior_match:
            for c in conditions:
                if type(c) is str:
                    accounted.add(c)
                elif "and" in c:
                    for c2 in c["and"]:
                        if type(c2) is str:
                            accounted.add(c2)

        return prior_match or not required

    def rule_broken_msg(self, rule):
        msg = ""
        if type(rule) is str:
            return f"{msg} {rule}"
        elif "and" in rule:
            msg = f"{msg} all of ["
            for sub in rule["and"]:
                msg = f"{msg} {self.rule_broken_msg(sub)}"
            return f"{msg} ]"
        elif "or" in rule:
            msg = f"{msg} at least one of ["
            for sub in rule["or"]:
                msg = f"{msg} {self.rule_broken_msg(sub)}"
            return f"{msg} ]"
        elif "xor" in rule:
            msg = f"{msg} only one of ["
            for sub in rule["xor"]:
                msg = f"{msg} {self.rule_broken_msg(sub)}"
            return f"{msg} ]"
        return "for reason unknown"

    def check_entity(self, entity, cfg):
        """
        Check that the entity has a dps list and each dps has an id,
        type and name, and any other consistency checks.
        """
        self.assertIsNotNone(
            entity._config.get("entity"), f"entity type missing in {cfg}"
        )
        e = entity.config_id
        self.assertIsNotNone(
            entity._config.get("dps"), f"dps missing from {e} in {cfg}"
        )
        functions = set()
        extra = set()
        known = set()
        redirects = set()

        # Basic checks of dps, and initialising of redirects and extras sets
        # for later checking
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
            extra.add(dp.name)
            mappings = dp._config.get("mapping", [])
            self.assertIsInstance(
                mappings,
                list,
                f"mapping is not a list in {cfg}; entity {e}, dp {dp.name}",
            )
            for m in mappings:
                conditions = m.get("conditions", [])
                self.assertIsInstance(
                    conditions,
                    list,
                    f"conditions is not a list in {cfg}; entity {e}, dp {dp.name}",
                )
                for c in conditions:
                    if c.get("value_redirect"):
                        redirects.add(c.get("value_redirect"))
                    if c.get("value_mirror"):
                        redirects.add(c.get("value_mirror"))
                if m.get("value_redirect"):
                    redirects.add(m.get("value_redirect"))
                if m.get("value_mirror"):
                    redirects.add(m.get("value_mirror"))

        # Check redirects all exist
        for redirect in redirects:
            self.assertIn(redirect, extra, f"dp {redirect} missing from {e} in {cfg}")

        # Check dps that are required for this entity type all exist
        expected = KNOWN_DPS.get(entity.entity)
        for rule in expected["required"]:
            self.assertTrue(
                self.dp_match(rule, functions, extra, known, True),
                f"{cfg} missing required {self.rule_broken_msg(rule)} in {e}",
            )

        for rule in expected["optional"]:
            self.assertTrue(
                self.dp_match(rule, functions, extra, known, False),
                f"{cfg} expecting {self.rule_broken_msg(rule)} in {e}",
            )

        # Check for potential typos in extra attributes
        known_extra = known - functions
        for attr in extra:
            for dp in known_extra:
                self.assertLess(
                    fuzz.ratio(attr, dp),
                    85,
                    f"Probable typo {attr} is too similar to {dp} in {cfg} {e}",
                )

        # Check that sensors with mapped values are of class enum and vice versa
        if entity.entity == "sensor":
            mock_device = MagicMock()
            sensor = TuyaLocalSensor(mock_device, entity)
            if sensor.options:
                self.assertEqual(
                    entity.device_class,
                    SensorDeviceClass.ENUM,
                    f"{cfg} {e} has mapped values but does not have a device class of enum",
                )
            if entity.device_class == SensorDeviceClass.ENUM:
                self.assertIsNotNone(
                    sensor.options,
                    f"{cfg} {e} has a device class of enum, but has no mapped values",
                )

    def test_config_files_parse(self):
        """
        All configs should be parsable and meet certain criteria
        """
        for cfg in available_configs():
            entities = []
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
            entities.append(parsed.primary_entity.config_id)
            secondary = False
            for entity in parsed.secondary_entities():
                secondary = True
                self.check_entity(entity, cfg)
                entities.append(entity.config_id)
            # check entities are unique
            self.assertCountEqual(entities, set(entities))

            # If there are no secondary entities, check that it is intended
            if not secondary:
                for key in parsed._config.keys():
                    self.assertFalse(
                        key.startswith("sec"),
                        f"misspelled secondary_entities in {cfg}",
                    )

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
        cfg = get_config("goldair_gpph_heater")
        error_code = cfg.primary_entity.find_dps("error")
        with self.assertRaises(TypeError):
            await error_code.async_set_value(mock_device, 1)

    def test_dps_values_is_empty_with_no_mapping(self):
        """
        Test that a dps with no mapping returns None as its possible values
        """
        mock_device = MagicMock()
        cfg = get_config("goldair_gpph_heater")
        temp = cfg.primary_entity.find_dps("current_temperature")
        self.assertEqual(temp.values(mock_device), [])

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

    def test_decoding_hex(self):
        """Test that decoded_value works with hex encoding."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "hex"}
        mock_device = MagicMock()
        mock_device.get_property.return_value = "babe"
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(
            cfg.decoded_value(mock_device),
            b"\xba\xbe",
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

    def test_encoding_hex(self):
        """Test that encode_value works with base64."""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "hex"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(cfg.encode_value(b"\xca\xfe"), "cafe")

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

    def test_get_device_id(self):
        """Test that check if device id is correct"""
        self.assertEqual("my-device-id", get_device_id({"device_id": "my-device-id"}))
        self.assertEqual("sub-id", get_device_id({"device_cid": "sub-id"}))
        self.assertEqual("s", get_device_id({"device_id": "d", "device_cid": "s"}))

    def test_getting_masked_hex(self):
        """Test that get_value works with masked hex encoding."""
        mock_entity = MagicMock()
        mock_config = {
            "id": "1",
            "name": "test",
            "type": "hex",
            "mapping": [
                {"mask": "ff00"},
            ],
        }
        mock_device = MagicMock()
        mock_device.get_property.return_value = "babe"
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(
            cfg.get_value(mock_device),
            0xBA,
        )

    def test_setting_masked_hex(self):
        """Test that get_values_to_set works with masked hex encoding."""
        mock_entity = MagicMock()
        mock_config = {
            "id": "1",
            "name": "test",
            "type": "hex",
            "mapping": [
                {"mask": "ff00"},
            ],
        }
        mock_device = MagicMock()
        mock_device.get_property.return_value = "babe"
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertEqual(
            cfg.get_values_to_set(mock_device, 0xCA),
            {"1": "cabe"},
        )

    def test_default_without_mapping(self):
        """Test that default returns None when there is no mapping"""
        mock_entity = MagicMock()
        mock_config = {"id": "1", "name": "test", "type": "string"}
        cfg = TuyaDpsConfig(mock_entity, mock_config)
        self.assertIsNone(cfg.default)
