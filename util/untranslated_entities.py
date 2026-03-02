"""Find entities with names that match existing translation keys."""

import json
import sys

from homeassistant.util import slugify

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def error_location(entity):
    return f"::error file=custom_components/tuya_local/devices/{entity._device.config},line={entity._config.__line__}:"


def main() -> int:
    with open("custom_components/tuya_local/translations/en.json", "r") as f:
        english = json.load(f)["entity"]
    detected = 0
    for config in available_configs():
        device = TuyaDeviceConfig(config)
        for entity in device.all_entities():
            key = entity.translation_key
            where = error_location(entity)
            if key and (
                entity.entity not in english or key not in english[entity.entity]
            ):
                print(f"{where}: translation_key {key} does not exist")
                detected += 1
                continue

            if entity.name is None:
                continue
            slug = slugify(entity.name)
            cls = entity.device_class

            if cls is not None and key is None and cls == slug:
                print(f"{where}: Entity name {entity.name} hides class translation.")
                detected += 1
                continue

            if entity.entity not in english:
                continue

            if entity.translation_key:
                if slug == entity.translation_key:
                    print(f"{where}: Entity name {entity.name} hides translation.")
                    detected += 1
                continue
            translations = english[entity.entity]
            if slug in translations:
                print(f"{where}: Entity can use translation_key: {slug}")
                detected += 1
    return detected


if __name__ == "__main__":
    sys.exit(main())
