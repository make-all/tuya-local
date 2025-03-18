"""Check products info"""

import sys

from custom_components.tuya_local.helpers.device_config import (
    TuyaDeviceConfig,
    available_configs,
)


def main():
    missing = False
    nameonly = False
    arg_supplied = False

    for arg in sys.argv[1:]:
        arg_supplied = True
        if arg == "--missing":
            missing = True
        elif arg == "--nameonly":
            nameonly = True
        else:
            print("List potential issues with products listings")
            print("")
            print(f"Usage: {sys.argv[0]} [--missing] [--nameonly]")
            exit(1)

    # default to nameonly if no arguments supplied
    if not arg_supplied:
        nameonly = True

    for config in available_configs():
        device = TuyaDeviceConfig(config)
        products = device._config.get("products", None)
        if products:
            for product in products:
                if (
                    product.get("name")
                    and not product.get("manufacturer")
                    and not product.get("model")
                ):
                    if nameonly:
                        print(
                            f"{config}: {product['name']} may need splitting to manufacturer and model"
                        )
        else:
            if missing:
                print(f"{config}: No products")


if __name__ == "__main__":
    sys.exit(main())
