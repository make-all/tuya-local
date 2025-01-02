"""Check for duplicates of the supplied file."""

import sys

from common_funcs import load_config, make_sample_dps

from custom_components.tuya_local.helpers.device_config import possible_matches


def main():
    for filename in sys.argv[1:]:
        config = load_config(filename)
        if config is None:
            print(f"No config could be loaded for {filename}")
            continue
        sample_dps = make_sample_dps(config)

        # device = FakeDevice(sample_dps)
        for m in possible_matches(sample_dps):
            if m.config_type == config.config_type:
                continue
            if m.match_quality(sample_dps) > 50:
                print(
                    f"{m.config_type} matched {filename} {m.match_quality(sample_dps)}%"
                )


if __name__ == "__main__":
    sys.exit(main())
