"""Find matching entities in config files."""

import sys

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def main() -> int:
    for config in available_configs():
        device = TuyaDeviceConfig(config)
        for entity in device.all_entities():
            if entity.config_id == sys.argv[1]:
                print(f"{config}:{entity._config.__line__}: found {entity.config_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
