"""Find translated selects with untranslated mappings in config files."""

import json
import sys

from common_funcs import FakeDevice

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def main() -> int:
    with open("custom_components/tuya_local/translations/en.json", "r") as f:
        english = json.load(f)
    select = english["entity"]["select"]
    dev = FakeDevice({})
    for config in available_configs():
        device = TuyaDeviceConfig(config)
        for entity in device.all_entities():
            if entity.entity == "select" and entity.translation_key:
                d = entity.find_dps("option")
                translations = select.get(entity.translation_key)
                if translations is None:
                    print(
                        f"{config}:{entity._config.__line__}: MISSING {entity.translation_key}"
                    )
                    continue
                for v in d.values(dev):
                    if v not in translations["state"]:
                        print(
                            f"{config}:{v.__line__}: {v} missing from {entity.translation_key}"
                        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
