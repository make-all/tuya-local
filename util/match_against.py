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


def main() -> int:
    dps = json.loads(" ".join(sys.argv[2:]))
    device = FakeDevice(dps)
    config = TuyaDeviceConfig(sys.argv[1])
    print(f"{config.primary_entity.config_id}:")
    for dp in config.primary_entity.dps():
        if dp.id not in dps.keys():
            print(f"    {dp.name} missing from data")
        elif not _typematch(dp.type, dps.get(dp.id)):
            print(
                f"    {dp.name} type mismatch, expected {dp.type.__name__}, got {dps.get(dp.id)}"
            )
        else:
            print(f"   {dp.name}: {dp.get_value(device)} from {dp.values(device)}")
    for entity in config.secondary_entities():
        print(f"{entity.config_id}:")
        for dp in entity.dps():
            if dp.id not in dps.keys():
                print(f"    {dp.name} missing from data")
            elif not _typematch(dp.type, dps.get(dp.id)):
                print(
                    f"    {dp.name} type mismatch, expected {dp.type.__name__}, got {dps.get(dp.id)}"
                )
            else:
                print(f"    {dp.name}: {dp.get_value(device)}")


if __name__ == "__main__":
    sys.exit(main())
