"""Find matching devices for the supplied dp list"""
import sys
import json

from custom_components.tuya_local.helpers.device_config import possible_matches


def main() -> int:
    dps = json.loads(" ".join(sys.argv[1:]))
    for match in possible_matches(dps):
        print(f"{match.config_type} matched {match.match_quality(dps)}%")


if __name__ == "__main__":
    sys.exit(main())
