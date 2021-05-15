"""Test the config parser"""
from custom_components.tuya_local.helpers.device_config import (
    available_configs,
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
)


def test_can_find_config_files():
    """Test that the config files can be found by the parser."""
    found = False
    for cfg in available_configs():
        found = True
        break
    assert found


def test_config_files_parse():
    for cfg in available_configs():
        parsed = TuyaDeviceConfig(cfg)
        assert parsed.name is not None


def test_config_files_have_legacy_link():
    """
       Initially, we require a link between the new style config, and the old
       classes so we can transition over to the new config.  When the
       transition is complete, we will drop the requirement, as new devices
       will only be added as config files.
    """
    for cfg in available_configs():
        parsed = TuyaDeviceConfig(cfg)
        assert parsed.primary_entity is not None
        assert parsed.primary_entity.legacy_device is not None
        for e in parsed.secondary_entities():
            assert e.legacy_device is not None


def test_gpph_heater_detection():
    """Test that the GPPH heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("goldair_gpph_heater.yaml")
    assert parsed.primary_entity.legacy_device == ".heater.climate.GoldairHeater"
    assert parsed.matches(GPPH_HEATER_PAYLOAD)


def test_gpcv_heater_detection():
    """Test that the GPCV heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("goldair_gpcv_heater.yaml")
    assert (
        parsed.primary_entity.legacy_device == ".gpcv_heater.climate.GoldairGPCVHeater"
    )
    assert parsed.matches(GPCV_HEATER_PAYLOAD)


def test_eurom_heater_detection():
    """Test that the Eurom heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("eurom_600_heater.yaml")
    assert (
        parsed.primary_entity.legacy_device
        == ".eurom_600_heater.climate.EuromMonSoleil600Heater"
    )
    assert parsed.matches(EUROM_600_HEATER_PAYLOAD)


def test_geco_heater_detection():
    """Test that the GECO heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("goldair_geco_heater.yaml")
    assert (
        parsed.primary_entity.legacy_device == ".geco_heater.climate.GoldairGECOHeater"
    )
    assert parsed.matches(GECO_HEATER_PAYLOAD)


def test_kogan_heater_detection():
    """Test that the Kogan heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("kogan_heater.yaml")
    assert parsed.primary_entity.legacy_device == ".kogan_heater.climate.KoganHeater"
    assert parsed.matches(KOGAN_HEATER_PAYLOAD)


def test_goldair_dehumidifier_detection():
    """Test that the Goldair dehumidifier can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("goldair_dehumidifier.yaml")
    assert (
        parsed.primary_entity.legacy_device
        == ".dehumidifier.climate.GoldairDehumidifier"
    )
    assert parsed.matches(DEHUMIDIFIER_PAYLOAD)


def test_goldair_fan_detection():
    """Test that the Goldair fan can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("goldair_fan.yaml")
    assert parsed.primary_entity.legacy_device == ".fan.climate.GoldairFan"
    assert parsed.matches(FAN_PAYLOAD)


def test_kogan_socket_detection():
    """Test that the 1st gen Kogan Socket can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("kogan_switch.yaml")
    assert (
        parsed.primary_entity.legacy_device == ".kogan_socket.switch.KoganSocketSwitch"
    )
    assert parsed.matches(KOGAN_SOCKET_PAYLOAD)


def test_kogan_socket2_detection():
    """Test that the 2nd gen Kogan Socket can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("kogan_switch2.yaml")
    assert (
        parsed.primary_entity.legacy_device == ".kogan_socket.switch.KoganSocketSwitch"
    )
    assert parsed.matches(KOGAN_SOCKET_PAYLOAD2)


def test_gsh_heater_detection():
    """Test that the GSH heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("andersson_gsh_heater.yaml")
    assert (
        parsed.primary_entity.legacy_device == ".gsh_heater.climate.AnderssonGSHHeater"
    )
    assert parsed.matches(GSH_HEATER_PAYLOAD)


def test_gardenpac_heatpump_detection():
    """Test that the GardenPac heatpump can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("gardenpac_heatpump.yaml")
    assert (
        parsed.primary_entity.legacy_device
        == ".gardenpac_heatpump.climate.GardenPACPoolHeatpump"
    )
    assert parsed.matches(GARDENPAC_HEATPUMP_PAYLOAD)


def test_purline_heater_detection():
    """Test that the Purline heater can be detected from its sample payload."""
    parsed = TuyaDeviceConfig("purline_m100_heater.yaml")
    assert (
        parsed.primary_entity.legacy_device
        == ".purline_m100_heater.climate.PurlineM100Heater"
    )
    assert parsed.matches(PURLINE_M100_HEATER_PAYLOAD)
