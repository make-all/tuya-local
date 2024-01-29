"""Find matching devices for the supplied dp list"""
import json
import sys

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    _typematch,
)


class FakeDevice:
    def __init__(self, dps):
        self._dps = dps

    def get_property(self, id):
        return self._dps.get(id)

    @property
    def name(self):
        return "cmdline"


def main() -> int:
    dps = json.loads(" ".join(sys.argv[2:]))
    device = FakeDevice(dps)
    config = TuyaDeviceConfig(sys.argv[1])
    print(f"{config.primary_entity.config_id}:")
    for dp in config.primary_entity.dps():
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
    for entity in config.secondary_entities():
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
