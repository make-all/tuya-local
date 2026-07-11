"""Tests for delta sensor entity."""

from unittest.mock import Mock

from custom_components.tuya_local.helpers.device_config import TuyaEntityConfig
from custom_components.tuya_local.sensor import TuyaLocalDeltaSensor


def make_delta_sensor(delta_function=None, averaging_window=None):
    """Create a delta sensor with real TuyaEntityConfig."""
    mock_device = Mock()

    config_dict = {
        "entity": "sensor",
        "mode": "delta",
        "dps": [
            {
                "id": 127,
                "name": "sensor",
                "type": "integer",
                "unit": "kWh",
                "mapping": [{"scale": 100}],
            },
            {
                "id": 128,
                "name": "delta_start_key",
                "type": "integer",
            },
            {
                "id": 129,
                "name": "delta_key",
                "type": "integer",
            },
        ],
    }

    if delta_function is not None:
        config_dict["delta_function"] = delta_function

    if averaging_window is not None:
        config_dict["averaging_window"] = averaging_window

    config = TuyaEntityConfig(mock_device, config_dict)
    sensor = TuyaLocalDeltaSensor(mock_device, config)

    return sensor


def patch_dp_values(monkeypatch, sensor):
    """Patch sensor DP reads and return mutable value storage."""
    values = {
        "sensor": None,
        "delta_start_key": None,
        "delta_key": None,
    }

    monkeypatch.setattr(sensor, "_get_dp_value", lambda name: values.get(name))

    return values


def set_dp_values(values, delta, start, end):
    """Set current mocked DP values.

    delta is already the scaled value in kWh, as returned by _get_dp_value().
    """
    values["sensor"] = delta
    values["delta_start_key"] = start
    values["delta_key"] = end


def test_delta_total_accumulates_intervals(monkeypatch):
    """Test that delta_function=total accumulates interval deltas."""
    sensor = make_delta_sensor("total")
    values = patch_dp_values(monkeypatch, sensor)

    result = []

    for delta, start, end in [
        (0.01, 0, 120),
        (0.02, 120, 240),
        (0.01, 240, 360),
    ]:
        set_dp_values(values, delta, start, end)
        result.append(sensor.native_value)

    assert result == [0.01, 0.03, 0.04]


def test_delta_total_does_not_count_same_key_twice(monkeypatch):
    """Test that repeated reads of the same interval are not counted twice."""
    sensor = make_delta_sensor("total")
    values = patch_dp_values(monkeypatch, sensor)

    set_dp_values(values, 0.01, 0, 120)

    assert sensor.native_value == 0.01
    assert sensor.native_value == 0.01
    assert sensor.native_value == 0.01


def test_delta_defaults_to_total_function(monkeypatch):
    """Test that delta_function defaults to total."""
    sensor = make_delta_sensor()
    values = patch_dp_values(monkeypatch, sensor)

    set_dp_values(values, 0.01, 0, 120)

    assert sensor._delta_function == "total"
    assert sensor.native_value == 0.01


def test_delta_average_power_uses_averaging_window(monkeypatch):
    """Test average power calculation over configured averaging window."""
    sensor = make_delta_sensor("average", averaging_window=600)
    values = patch_dp_values(monkeypatch, sensor)

    result = []

    for delta, start, end in [
        (0.01, 0, 120),
        (0.02, 120, 240),
        (0.01, 240, 360),
        (0.00, 360, 480),
        (0.01, 480, 600),
        (0.00, 600, 720),
    ]:
        set_dp_values(values, delta, start, end)
        result.append(sensor.native_value)

    assert result == [
        300.0,  # 0.01 kWh / 120 s
        450.0,  # 0.03 kWh / 240 s
        400.0,  # 0.04 kWh / 360 s
        300.0,  # 0.04 kWh / 480 s
        300.0,  # 0.05 kWh / 600 s
        240.0,  # first sample purged: 0.04 kWh / 600 s
    ]


def test_delta_average_zero_window_uses_last_interval_only(monkeypatch):
    """Test averaging_window=0 returns only the last interval average."""
    sensor = make_delta_sensor("average", averaging_window=0)
    values = patch_dp_values(monkeypatch, sensor)

    set_dp_values(values, 0.01, 0, 120)
    assert sensor.native_value == 300.0

    set_dp_values(values, 0.02, 120, 240)
    assert sensor.native_value == 600.0


def test_invalid_delta_function_falls_back_to_total(monkeypatch):
    """Test invalid delta_function fallback."""
    sensor = make_delta_sensor("invalid")
    values = patch_dp_values(monkeypatch, sensor)

    set_dp_values(values, 0.01, 0, 120)

    assert sensor._delta_function == "total"
    assert sensor.native_value == 0.01
