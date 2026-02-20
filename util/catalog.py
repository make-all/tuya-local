#!/usr/bin/python3
"""Build a catalog of supported devices/entities

This script was created to check for entity ids that change between versions.
The script needs to be run on the version before a potential id changing
modification, then again after to compare the two outputs.
"""

import sys

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def main() -> int:
    print("Catalog================")
    for config in available_configs():
        device = TuyaDeviceConfig(config)
        for entity in device.all_entities():
            print(f"{config}: {entity.config_id}")


if __name__ == "__main__":
    sys.exit(main())
