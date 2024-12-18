"""Common functions used in the utilities."""

from custom_components.tuya_local.helpers.device_config import (
    get_config,
)


class FakeDevice:
    def __init__(self, dps):
        self._dps = dps

    def get_property(self, id):
        return self._dps.get(id)

    @property
    def name(self):
        return "cmdline"


def load_config(filename):
    """Load the config for the device."""
    if filename.endswith(".yaml"):
        filename = filename[:-5]
    if "/" in filename:
        filename = filename.split("/")[-1]

    return get_config(filename)


def representation(dp):
    """Return a represenative value for the dp."""
    if dp.type is bool:
        return True
    if dp.type is int:
        if dp._config.get(range):
            return dp._config.get(range)["min"]
        return 0
    if dp.type is str:
        return ""
    if dp.type is float:
        return 0.0


def make_sample_dps(config):
    """Return a dictionary of sample DPS values."""
    all_dps = config._get_all_dps()
    return {dp.id: representation(dp) for dp in all_dps}
