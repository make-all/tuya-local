"""Test the config parser"""

import pytest
import voluptuous as vol
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
from .helpers import assert_device_properties_set, mock_device

PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required("id"): str,
        vol.Optional("name"): str,
        vol.Optional("manufacturer"): str,
        vol.Optional("model"): str,
        vol.Optional("model_id"): str,
    }
)
CONDMAP_SCHEMA = vol.Schema(
    {
        vol.Optional("dps_val"): vol.Maybe(vol.Any(str, int, bool, list)),
        vol.Optional("value"): vol.Maybe(vol.Any(str, int, bool, float)),
        vol.Optional("value_redirect"): str,
        vol.Optional("value_mirror"): str,
        vol.Optional("available"): str,
        vol.Optional("range"): {
            vol.Required("min"): int,
            vol.Required("max"): int,
        },
        vol.Optional("target_range"): {
            vol.Required("min"): int,
            vol.Required("max"): int,
        },
        vol.Optional("scale"): vol.Any(int, float),
        vol.Optional("step"): vol.Any(int, float),
        vol.Optional("invert"): True,
        vol.Optional("unit"): str,
        vol.Optional("icon"): vol.Match(r"^mdi:"),
        vol.Optional("icon_priority"): int,
        vol.Optional("hidden"): True,
        vol.Optional("invalid"): True,
        vol.Optional("default"): True,
    }
)
COND_SCHEMA = CONDMAP_SCHEMA.extend(
    {
        vol.Required("dps_val"): vol.Maybe(vol.Any(str, int, bool, list)),
        vol.Optional("mapping"): [CONDMAP_SCHEMA],
    }
)
MAPPING_SCHEMA = CONDMAP_SCHEMA.extend(
    {
        vol.Optional("constraint"): str,
        vol.Optional("conditions"): [COND_SCHEMA],
    }
)
FORMAT_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("bytes"): int,
        vol.Optional("range"): {
            vol.Required("min"): int,
            vol.Required("max"): int,
        },
    }
)
DP_SCHEMA = vol.Schema(
    {
        vol.Required("id"): int,
        vol.Required("type"): vol.In(
            [
                "string",
                "integer",
                "boolean",
                "hex",
                "base64",
                "bitfield",
                "unixtime",
                "json",
                "utf16b64",
            ]
        ),
        vol.Required("name"): str,
        vol.Optional("range"): {
            vol.Required("min"): int,
            vol.Required("max"): int,
        },
        vol.Optional("unit"): str,
        vol.Optional("precision"): vol.Any(int, float),
        vol.Optional("class"): vol.In(
            [
                "measurement",
                "measurement_angle",
                "total",
                "total_increasing",
            ]
        ),
        vol.Optional("optional"): True,
        vol.Optional("persist"): False,
        vol.Optional("hidden"): True,
        vol.Optional("readonly"): True,
        vol.Optional("sensitive"): True,
        vol.Optional("force"): True,
        vol.Optional("icon_priority"): int,
        vol.Optional("mapping"): [MAPPING_SCHEMA],
        vol.Optional("format"): [FORMAT_SCHEMA],
        vol.Optional("mask"): str,
        vol.Optional("endianness"): vol.In(["little"]),
        vol.Optional("mask_signed"): True,
    }
)
ENTITY_SCHEMA = vol.Schema(
    {
        vol.Required("entity"): vol.In(
            [
                "alarm_control_panel",
                "binary_sensor",
                "button",
                "camera",
                "climate",
                "cover",
                "datetime",
                "event",
                "fan",
                "humidifier",
                "infrared",
                "lawn_mower",
                "light",
                "lock",
                "number",
                "remote",
                "select",
                "sensor",
                "siren",
                "switch",
                "text",
                "time",
                "vacuum",
                "valve",
                "water_heater",
            ]
        ),
        vol.Optional("name"): str,
        vol.Optional("class"): str,
        vol.Optional(vol.Or("translation_key", "translation_only_key")): str,
        vol.Optional("translation_placeholders"): dict[str, str],
        vol.Optional("category"): vol.In(["config", "diagnostic"]),
        vol.Optional("icon"): vol.Match(r"^mdi:"),
        vol.Optional("icon_priority"): int,
        vol.Optional("deprecated"): str,
        vol.Optional("mode"): vol.In(["box", "slider"]),
        vol.Optional("hidden"): vol.In([True, "unavailable"]),
        vol.Required("dps"): [DP_SCHEMA],
    }
)
YAML_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Optional("legacy_type"): str,
        vol.Optional("products"): [PRODUCT_SCHEMA],
        vol.Required("entities"): [ENTITY_SCHEMA],
    }
)

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
    "datetime": {
        "required": [{"or": ["year", "month", "day", "hour", "minute", "second"]}],
        "optional": [],
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
    "infrared": {
        "required": ["send"],
        "optional": ["control", "code_type", "delay"],
    },
    "lawn_mower": {"required": ["activity", "command"], "optional": []},
    "light": {
        "required": [{"or": ["switch", "brightness", "effect"]}],
        "optional": ["color_mode", "color_temp", {"xor": ["rgbhsv", "named_color"]}],
    },
    "lock": {
        "required": [],
        "optional": [
            "lock",
            "lock_state",
            "code_unlock",
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
        "optional": ["unit", "minimum", "maximum", "decimal"],
    },
    "remote": {
        "required": ["send"],
        "optional": ["receive", "command", "type", "head"],
    },
    "select": {"required": ["option"], "optional": []},
    "sensor": {"required": ["sensor"], "optional": ["unit"]},
    "siren": {
        "required": [],
        "optional": ["tone", "volume", "duration", "switch"],
    },
    "switch": {"required": ["switch"], "optional": ["current_power_w"]},
    "text": {"required": ["value"], "optional": []},
    "time": {"required": [{"or": ["hour", "minute", "second", "hms"]}], "optional": []},
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
    "valve": {
        "required": ["valve"],
        "optional": ["switch"],
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


def test_can_find_config_files():
    """Test that the config files can be found by the parser."""
    found = False
    for _ in available_configs():
        found = True
        break
    assert found


def dp_match(condition, accounted, unaccounted, known, required=False):
    if isinstance(condition, str):
        known.add(condition)
        if condition in unaccounted:
            unaccounted.remove(condition)
            accounted.add(condition)
        if required:
            return condition in accounted
        else:
            return True
    elif "and" in condition:
        return and_match(condition["and"], accounted, unaccounted, known, required)
    elif "or" in condition:
        return or_match(condition["or"], accounted, unaccounted, known)
    elif "xor" in condition:
        return xor_match(condition["xor"], accounted, unaccounted, known, required)
    else:
        pytest.fail(f"Unrecognized condition {condition}")


def and_match(conditions, accounted, unaccounted, known, required):
    single_match = False
    all_match = True
    for cond in conditions:
        match = dp_match(cond, accounted, unaccounted, known, True)
        all_match = all_match and match
        single_match = single_match or match
    if required:
        return all_match
    else:
        return all_match == single_match


def or_match(conditions, accounted, unaccounted, known):
    match = False
    # loop through all, to ensure they are transferred to accounted list
    for cond in conditions:
        match = match or dp_match(cond, accounted, unaccounted, known, True)
    return match


def xor_match(conditions, accounted, unaccounted, known, required):
    prior_match = False
    for cond in conditions:
        match = dp_match(cond, accounted, unaccounted, known, True)

        if match and prior_match:
            return False
        prior_match = prior_match or match

    # If any matched, all should be considered matched
    # this bit only handles nesting "and" within "xor"

    if prior_match:
        for c in conditions:
            if isinstance(c, str):
                accounted.add(c)
            elif "and" in c:
                for c2 in c["and"]:
                    if isinstance(c2, str):
                        accounted.add(c2)

    return prior_match or not required


def rule_broken_msg(rule):
    msg = ""
    if isinstance(rule, str):
        return f"{msg} {rule}"
    elif "and" in rule:
        msg = f"{msg} all of ["
        for sub in rule["and"]:
            msg = f"{msg} {rule_broken_msg(sub)}"
        return f"{msg} ]"
    elif "or" in rule:
        msg = f"{msg} at least one of ["
        for sub in rule["or"]:
            msg = f"{msg} {rule_broken_msg(sub)}"
        return f"{msg} ]"
    elif "xor" in rule:
        msg = f"{msg} only one of ["
        for sub in rule["xor"]:
            msg = f"{msg} {rule_broken_msg(sub)}"
        return f"{msg} ]"
    return "for reason unknown"


def check_entity(entity, cfg, mocker):
    """
    Check that the entity has a dps list and each dps has an id,
    type and name, and any other consistency checks.
    """
    fname = f"custom_components/tuya_local/devices/{cfg}"
    line = entity._config.__line__
    assert entity._config.get("entity") is not None, (
        f"\n::error file={fname},line={line}::entity type missing in {cfg}"
    )
    e = entity.config_id
    assert entity._config.get("dps") is not None, (
        f"\n::error file={fname},line={line}::dps missing from {e} in {cfg}"
    )
    functions = set()
    extra = set()
    known = set()
    redirects = set()

    # Basic checks of dps, and initialising of redirects and extras sets
    # for later checking
    for dp in entity.dps():
        line = dp._config.__line__
        assert dp._config.get("id") is not None, (
            f"\n::error file={fname},line={line}::dp id missing from {e} in {cfg}"
        )
        assert dp._config.get("type") is not None, (
            f"\n::error file={fname},line={line}::dp type missing from {e} in {cfg}"
        )
        assert dp._config.get("name") is not None, (
            f"\n::error file={fname},line={line}::dp name missing from {e} in {cfg}"
        )
        extra.add(dp.name)
        mappings = dp._config.get("mapping", [])
        assert isinstance(mappings, list), (
            f"\n::error file={fname},line={line}::mapping is not a list in {cfg}; entity {e}, dp {dp.name}"
        )
        for m in mappings:
            line = m.__line__
            conditions = m.get("conditions", [])
            assert isinstance(conditions, list), (
                f"\n::error file={fname},line={line}::conditions is not a list in {cfg}; entity {e}, dp {dp.name}"
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

    line = entity._config.__line__
    # Check redirects all exist
    for redirect in redirects:
        assert redirect in extra, (
            f"\n::error file={fname},line={line}::dp {redirect} missing from {e} in {cfg}"
        )

    # Check dps that are required for this entity type all exist
    expected = KNOWN_DPS.get(entity.entity)
    for rule in expected["required"]:
        assert dp_match(rule, functions, extra, known, True), (
            f"\n::error file={fname},line={line}::{cfg} missing required {rule_broken_msg(rule)} in {e}"
        )

    for rule in expected["optional"]:
        assert dp_match(rule, functions, extra, known, False), (
            f"\n::error file={fname},line={line}::{cfg} expecting {rule_broken_msg(rule)} in {e}"
        )

    # Check for potential typos in extra attributes
    known_extra = known - functions
    for attr in extra:
        for dp in known_extra:
            assert fuzz.ratio(attr, dp) < 85, (
                f"\n::error file={fname},line={line}::Probable typo {attr} is too similar to {dp} in {cfg} {e}"
            )

    # Check that sensors with mapped values are of class enum and vice versa
    if entity.entity == "sensor":
        mock_device = mocker.MagicMock()
        sensor = TuyaLocalSensor(mock_device, entity)
        if sensor.options:
            assert entity.device_class == SensorDeviceClass.ENUM, (
                f"\n::error file={fname},line={line}::{cfg} {e} has mapped values but does not have a device class of enum"
            )
        if entity.device_class == SensorDeviceClass.ENUM:
            assert sensor.options is not None, (
                f"\n::error file={fname},line={line}::{cfg} {e} has a device class of enum, but has no mapped values"
            )


def test_config_files_parse(mocker):
    """
    All configs should be parsable and meet certain criteria
    """
    for cfg in available_configs():
        entities = []
        parsed = TuyaDeviceConfig(cfg)
        # Check for error messages or unparsed config
        if isinstance(parsed, str) or isinstance(parsed._config, str):
            pytest.fail(f"unparsable yaml in {cfg}")

        fname = f"custom_components/tuya_local/devices/{cfg}"
        try:
            YAML_SCHEMA(parsed._config)
        except vol.MultipleInvalid as e:
            messages = []
            first_line = None
            for err in e.errors:
                path = ".".join([str(p) for p in err.path])
                messages.append(f"{path}: {err.msg}")
                if first_line is None:
                    # voluptuous doesn't always seem to return line numbers
                    if err.path and hasattr(err.path[-1], "__line__"):
                        first_line = err.path[-1].__line__

            messages = "; ".join(messages)
            if not first_line:
                first_line = 1
            pytest.fail(
                f"\n::error file={fname},line={first_line}::Validation error: {messages}"
            )

        assert parsed._config.get("name") is not None, (
            f"\n::error file={fname},line=1::name missing from {cfg}"
        )
        count = 0
        for entity in parsed.all_entities():
            check_entity(entity, cfg, mocker)
            # check entities are unique
            if entity.config_id in entities:
                pytest.fail(
                    f"\n::error file={fname},line={entity._config.__line__}::"
                    "Duplicate entity {entity.config_id} in {cfg}"
                )
            entities.append(entity.config_id)

            count += 1
        assert count > 0, f"\n::error file={fname},line=1::No entities found in {cfg}"


def test_configs_can_be_matched():
    """Test that the config files can be matched to a device."""
    for cfg in available_configs():
        optional = set()
        required = set()
        parsed = TuyaDeviceConfig(cfg)
        fname = f"custom_components/tuya_local/devices/{cfg}"
        products = parsed._config.get("products")
        # Configs with a product list can be matched by product id
        if products:
            p_match = False
            for p in products:
                if p.get("id"):
                    p_match = True
            if p_match:
                continue

        for entity in parsed.all_entities():
            for dp in entity.dps():
                if dp.optional:
                    optional.add(dp.id)
                else:
                    required.add(dp.id)

        assert len(required) > 0, (
            f"\n::error file={fname},line=1::No required dps found in {cfg}"
        )

        for dp in required:
            assert dp not in optional, (
                f"\n::error file={fname},line=1::Optional dp {dp} is required in {cfg}"
            )


# Most of the device_config functionality is exercised during testing of
# the various supported devices.  These tests concentrate only on the gaps.


def test_match_quality():
    """Test the match_quality function."""

    cfg = get_config("deta_fan")
    q = cfg.match_quality({**KOGAN_HEATER_PAYLOAD, "updated_at": 0})

    assert q == 0
    q = cfg.match_quality({**GPPH_HEATER_PAYLOAD})
    assert q == 0


def test_entity_find_unknown_dps_fails():
    """Test that finding a dps that doesn't exist fails."""
    cfg = get_config("kogan_switch")
    for entity in cfg.all_entities():
        non_existing = entity.find_dps("missing")
        assert non_existing is None
        break


@pytest.mark.asyncio
async def test_dps_async_set_readonly_value_fails(mocker):
    """Test that setting a readonly dps fails."""
    mock_device = mocker.MagicMock()
    cfg = get_config("aquatech_x6_water_heater")
    for entity in cfg.all_entities():
        if entity.entity == "climate":
            temp = entity.find_dps("temperature")
            with pytest.raises(TypeError):
                await temp.async_set_value(mock_device, 20)
            break


def test_dps_values_is_empty_with_no_mapping(mocker):
    """
    Test that a dps with no mapping returns empty list for possible values
    """
    mock_device = mocker.MagicMock()
    cfg = get_config("goldair_gpph_heater")
    for entity in cfg.all_entities():
        if entity.entity == "climate":
            temp = entity.find_dps("current_temperature")
            assert temp.values(mock_device) == []
            break


def test_config_returned():
    """Test that config file is returned by config"""
    cfg = get_config("kogan_switch")
    assert cfg.config == "smartplugv1.yaml"


def test_float_matches_ints():
    """Test that the _typematch function matches int values to float dps"""
    assert _typematch(float, 1)


def test_bytes_to_fmt_returns_string_for_unknown():
    """
    Test that the _bytes_to_fmt function parses unknown number of bytes
    as a string format.
    """
    assert _bytes_to_fmt(5) == "5s"


def test_deprecation(mocker):
    """Test that deprecation messages are picked from the config."""
    mock_device = mocker.MagicMock()
    mock_device.name = "Testing"
    mock_config = {"entity": "Test", "deprecated": "Passed"}
    cfg = TuyaEntityConfig(mock_device, mock_config)
    assert cfg.deprecated
    assert (
        cfg.deprecation_message
        == "The use of Test for Testing is deprecated and should be replaced by Passed."
    )


def test_format_with_none_defined(mocker):
    """Test that format returns None when there is none configured."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "string"}
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.format is None


def test_decoding_base64(mocker):
    """Test that decoded_value works with base64 encoding."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "base64"}
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = "VGVzdA=="
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.decoded_value(mock_device) == bytes("Test", "utf-8")


def test_decoding_hex(mocker):
    """Test that decoded_value works with hex encoding."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "hex"}
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = "babe"
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.decoded_value(mock_device) == b"\xba\xbe"


def test_decoding_unencoded(mocker):
    """Test that decoded_value returns the raw value when not encoded."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "string"}
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = "VGVzdA=="
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.decoded_value(mock_device) == "VGVzdA=="


def test_encoding_base64(mocker):
    """Test that encode_value works with base64."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "base64"}
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.encode_value(bytes("Test", "utf-8")) == "VGVzdA=="


def test_encoding_hex(mocker):
    """Test that encode_value works with base64."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "hex"}
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.encode_value(b"\xca\xfe") == "cafe"


def test_encoding_unencoded(mocker):
    """Test that encode_value works with base64."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "string"}
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.encode_value("Test") == "Test"


def test_match_returns_false_on_errors_with_bitfield(mocker):
    """Test that TypeError and ValueError cause match to return False."""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "bitfield"}
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert not cfg._match(15, "not an integer")


def test_values_with_mirror(mocker):
    """Test that value_mirror redirects."""
    mock_entity = mocker.MagicMock()
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
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = "1"
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    mapping = TuyaDpsConfig(mock_entity, mock_map_config)
    mock_entity.find_dps.return_value = mapping

    assert set(cfg.values(mock_device)) == {"unmirrored", "map_one", "map_two"}
    assert len(cfg.values(mock_device)) == 3


def test_get_device_id():
    """Test that check if device id is correct"""
    assert "my-device-id" == get_device_id({"device_id": "my-device-id"})
    assert "sub-id" == get_device_id({"device_cid": "sub-id"})
    assert "s" == get_device_id({"device_id": "d", "device_cid": "s"})


def test_getting_masked_hex(mocker):
    """Test that get_value works with masked hex encoding."""
    mock_entity = mocker.MagicMock()
    mock_config = {
        "id": "1",
        "name": "test",
        "type": "hex",
        "mask": "ff00",
    }
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = "babe"
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.get_value(mock_device) == 0xBA


def test_setting_masked_hex(mocker):
    """Test that get_values_to_set works with masked hex encoding."""
    mock_entity = mocker.MagicMock()
    mock_config = {
        "id": "1",
        "name": "test",
        "type": "hex",
        "mask": "ff00",
    }
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = "babe"
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.get_values_to_set(mock_device, 0xCA) == {"1": "cabe"}


def test_default_without_mapping(mocker):
    """Test that default returns None when there is no mapping"""
    mock_entity = mocker.MagicMock()
    mock_config = {"id": "1", "name": "test", "type": "string"}
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.default is None


def test_matching_with_product_id():
    """Test that matching with product id works"""
    cfg = get_config("smartplugv1")
    assert cfg.matches({}, ["37mnhia3pojleqfh"])


def test_matched_product_id_with_conflict_rejected():
    """Test that matching with product id fails when there is a conflict"""
    cfg = get_config("smartplugv1")
    assert not cfg.matches({"1": "wrong_type"}, ["37mnhia3pojleqfh"])


def test_multi_stage_redirect(mocker):
    """Test that multi stage redirects work correctly for read."""

    # Redirect used to combine multiple dps into a single value
    kc_cfg = get_config("kcvents_vt501_fan")
    for entity in kc_cfg.all_entities():
        if entity.entity == "fan":
            fan = entity
            break
    assert fan is not None
    speed = fan.find_dps("speed")
    assert speed is not None
    dps = {"1": True, "101": True, "102": False, "103": False}
    device = mock_device(dps, mocker)
    assert speed.values(device) == [33, 66, 100]
    assert speed.get_value(device) == 33
    dps["101"] = False
    dps["102"] = True
    assert speed.get_value(device) == 66
    dps["102"] = False
    dps["103"] = True
    assert speed.get_value(device) == 100

    # Redirect used for alternate dps
    dewin_cfg = get_config("dewin_kws306wf_energymeter")
    for entity in dewin_cfg.all_entities():
        if entity.entity == "switch" and entity.name is None:
            switch = entity
            break
    assert switch is not None
    main = switch.find_dps("switch")
    alt = switch.find_dps("alt")
    assert main is not None and alt is not None
    dps = {"16": True, "141": None}
    device = mock_device(dps, mocker)
    assert main.get_value(device) is True
    dps["16"] = False
    assert main.get_value(device) is False
    dps["141"] = True
    dps["16"] = None
    assert main.get_value(device) is True
    dps["141"] = False
    assert main.get_value(device) is False


@pytest.mark.asyncio
async def test_setting_multi_stage_redirect(mocker):
    """Test that multi stage redirects work correctly for write."""

    # Redirect used to combine multiple dps into a single value
    kc_cfg = get_config("kcvents_vt501_fan")
    for entity in kc_cfg.all_entities():
        if entity.entity == "fan":
            fan = entity
            break
    assert fan is not None
    speed = fan.find_dps("speed")
    assert speed is not None
    dps = {"1": True, "101": True, "102": False, "103": False}
    device = mock_device(dps, mocker)
    async with assert_device_properties_set(device, {"102": True}):
        await speed.async_set_value(device, 66)
    async with assert_device_properties_set(device, {"103": True}):
        await speed.async_set_value(device, 100)

    # Redirect used for alternate dps
    dewin_cfg = get_config("dewin_kws306wf_energymeter")
    for entity in dewin_cfg.all_entities():
        if entity.entity == "switch" and entity.name is None:
            switch = entity
            break
    assert switch is not None
    main = switch.find_dps("switch")
    alt = switch.find_dps("alt")
    assert main is not None and alt is not None
    dps = {"16": True, "141": None}
    device = mock_device(dps, mocker)
    async with assert_device_properties_set(device, {"16": False}):
        await main.async_set_value(device, False)
    dps["16"] = None
    dps["141"] = True
    async with assert_device_properties_set(device, {"141": False}):
        await main.async_set_value(device, False)


def test_reading_target_range(mocker):
    """Test reading a number that has a target range."""
    mock_config = {
        "id": 1,
        "name": "test",
        "type": "integer",
        "range": {"min": 0, "max": 16},
        "mapping": [{"target_range": {"min": 0, "max": 100}}],
    }
    mock_entity = mocker.MagicMock()
    mock_device = mocker.MagicMock()
    mock_device.get_property.return_value = 8
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.get_value(mock_device) == 50


def test_writing_target_range(mocker):
    """Test writing a number that has a target range."""
    mock_config = {
        "id": 1,
        "name": "test",
        "type": "integer",
        "range": {"min": 0, "max": 16},
        "mapping": [{"target_range": {"min": 0, "max": 100}}],
    }
    mock_entity = mocker.MagicMock()
    mock_device = mocker.MagicMock()
    cfg = TuyaDpsConfig(mock_entity, mock_config)
    assert cfg.get_values_to_set(mock_device, 100) == {"1": 16}
