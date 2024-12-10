"""Check for duplicates of the supplied file."""

import sys

from custom_components.tuya_local.helpers.device_config import (
    get_config,
    possible_matches,
)


class FakeDevice:
    def __init__(self, dps):
        self._dps = dps

    def get_property(self, id):
        return self._dps.get(id)

    @property
    def name(self):
        return "cmdline"


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


def main():
    for filename in sys.argv[1:]:
        if filename.endswith(".yaml"):
            filename = filename[:-5]
        if "/" in filename:
            filename = filename.split("/")[-1]

        config = get_config(filename)
        all_dps = config._get_all_dps()
        sample_dps = {dp.id: representation(dp) for dp in all_dps}

        # device = FakeDevice(sample_dps)
        for m in possible_matches(sample_dps):
            if m.config_type == filename:
                continue
            if m.match_quality(sample_dps) > 50:
                print(
                    f"{m.config_type} matched {filename} {m.match_quality(sample_dps)}%"
                )


if __name__ == "__main__":
    sys.exit(main())
