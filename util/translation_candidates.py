#!/usr/bin/python3
"""Build a list of candidates for translation

This script was created to prioritise common entities for translation.
"""

import sys

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def main() -> int:
    candidates: dict[str, int] = {}

    for config in available_configs():
        device = TuyaDeviceConfig(config)
        for entity in device.all_entities():
            if entity.name:
                if entity.config_id in candidates:
                    candidates[entity.config_id] += 1
                else:
                    candidates[entity.config_id] = 1

    sorted_candidates = sorted(
        candidates.items(), key=lambda item: item[1], reverse=True
    )
    for candidate, count in sorted_candidates:
        print(f"{candidate}: {count}")


if __name__ == "__main__":
    sys.exit(main())
