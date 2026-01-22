"""Find entities with names that match existing translation keys."""

import json
import sys

from homeassistant.util import slugify

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def main() -> int:
    with open("custom_components/tuya_local/translations/en.json", "r") as f:
        english = json.load(f)
    for config in available_configs():
        device = TuyaDeviceConfig(config)
        for entity in device.all_entities():
            if (
                entity.translation_key
                or entity.name is None
                or entity.entity not in english["entity"]
            ):
                continue
            translations = english["entity"][entity.entity]
            slug = slugify(entity.name)
            if slug in translations:
                print(
                    f"{config}:{entity._config.__line__}: can use translation_key: {slug}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
