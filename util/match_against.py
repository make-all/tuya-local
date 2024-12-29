"""Find matching devices for the supplied dp list"""

import json
import sys

from common_funcs import FakeDevice, load_config

from custom_components.tuya_local.helpers.device_config import _typematch


def main() -> int:
    dps = json.loads(" ".join(sys.argv[2:]))
    device = FakeDevice(dps)
    config = load_config(sys.argv[1])
    if config is None:
        print(f"No config could be loaded for {sys.argv[1]}")
        return 1
    for entity in config.all_entities():
        print(f"{entity.config_id}:")
        for dp in entity.dps():
            if dp.id not in dps.keys():
                print(f"   {dp.name} missing from data")
                if not dp.optional:
                    print(f">> dp {dp.id} is REQUIRED!!!!")
            elif not _typematch(dp.type, dps.get(dp.id)):
                print(
                    f">> {dp.name} type MISMATCH, expected {dp.type.__name__}, got {dps.get(dp.id)}!!!"
                )
            else:
                values = dp.values(device)
                if values:
                    values = f" from {values}"
                else:
                    values = ""
                print(f"   {dp.name}: {dp.get_value(device)}{values}")


if __name__ == "__main__":
    sys.exit(main())
