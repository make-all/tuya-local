"""Find matching devices for the supplied dp list"""

import json
import sys

from common_funcs import FakeDevice

from custom_components.tuya_local.helpers.device_config import possible_matches


def main() -> int:
    dps = json.loads(" ".join(sys.argv[1:]))
    device = FakeDevice(dps)
    best = 0
    best_matches = set()

    for m in possible_matches(dps):
        if m.match_quality(dps) > best:
            best_matches.clear()
            best = m.match_quality(dps)

        if m.match_quality(dps) == best:
            best_matches.add(m)

    for m in best_matches:
        dps_seen = set(dps.keys())
        print(f"{m.config_type} matched {m.match_quality(dps)}%")
        for entity in m.all_entities():
            print(f"  {entity.config_id}:")
            for dp in entity.dps():
                dps_seen.discard(dp.id)
                print(f"    {dp.name}: {dp.get_value(device)}")
        for dp in dps_seen:
            print(f"  Missing {dp}: {dps[dp]}")


if __name__ == "__main__":
    sys.exit(main())
