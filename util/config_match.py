"""Find matching devices for the supplied dp list"""
import json
import sys

from custom_components.tuya_local.helpers.device_config import possible_matches


class FakeDevice:
    def __init__(self, dps):
        self._dps = dps

    def get_property(self, id):
        return self._dps.get(id)


def main() -> int:
    dps = json.loads(" ".join(sys.argv[1:]))
    device = FakeDevice(dps)

    for match in possible_matches(dps):
        print(f"{match.config_type} matched {match.match_quality(dps)}%")
        print(f"  {match.primary_entity.config_id}:")
        for dp in match.primary_entity.dps():
            print(f"   {dp.name}: {dp.get_value(device)}")
        for entity in match.secondary_entities():
            print(f"  {entity.config_id}:")
            for dp in entity.dps():
                print(f"    {dp.name}: {dp.get_value(device)}")


if __name__ == "__main__":
    sys.exit(main())
