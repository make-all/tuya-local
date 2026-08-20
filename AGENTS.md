# Instructions for autonomous agents

## Development environment

- This project is a Home Assistant integration.
- The source languages are Python, YAML and JSON
- package management is using `uv`
  If it is not already installed, it can be installed using:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```
- Use `uv run ...` to run commands on the project

## Coding standards

- Python files should be checked with `uv run ruff check`, `uv run ruff check --select -I`
- Python files should be formatted consistently with `uv run ruff format`
- YAML files for device configuration should be checked with `uv run yamllint`
- YAML files for device configuration must be located in the custom_components/tuya_local/devices folder
- Python files implementing the HA integration must be located in custom_components/tuya_local and its subfolders, with unit tests in tests and its subfolders.
- JSON files for translations are located in the custom_components/tuya_local/translations folder.
- Icons for translation keys are defined in custom_components/tuya_local/icons.json, and use icons from the material design icons at https://pictogrammers.com/library/mdi/
- Where possible, new devices should use existing translation_keys which are present in custom_components/tuya_local/translations/*.json and custom/components/tuya_local/icons.json
- if new translation_keys are added, they should be generic, not device specific, and translations in the appropriate language should be added to all files in custom_components/tuya_local/translations and relevant icons to custom_components/tuya_local/icons.json. It is best to submit additional translations as a separate PR request from new device submissions, as they can involve a lot of rework to existing configs.
- Device and entity names should follow the Home Assistant naming guidelines. Only the first word should be capitalised.
- Try to keep device and entity names concise.
- Top level names should be unbranded and without redundant words like "Smart" or "WiFi".

## Information gathering for new device configs

- When an unsupported device is attempted to be added to this integration, a WARNING level log message containing "LOCAL DPS" is output. This is essential information to determine which dps are present when the device is discovered by this integration. Any dps that are not present in this log message must be marked with `optional: true` in the config so that they are not required for matching.
- The Tuya developer platform is accessible at https://platform.tuya.com. The user should sign up for an account to get access to detailed information about their device.
- The DEVICE_ID for the user's device is required. They can get this from their list of devices in the Tuya developer portal, or from `tinytuya scan`.
- Product id for inclusion in the products section is available from the "Query Device Details" API call in the Cloud API Explorer on https://platform.tuya.com. This is also available as an api call at https://openapi.tuyaus.com/v2.0/cloud/thing/${DEVICE_ID} with some complex authentication. tuyaus may be tuyaeu or another string depending on region. If the region is wrong, a "space permission" error will result.
- Full dps information is available from the "Query Things Data Model" API call in the Cloud API Explorer on https://platform.tuya.com. This is also available as an api call at https://openapi.tuyaus.com/v2.0/cloud/thing/${DEVICE_ID}/model with some complex authentication. tuyaus may be tuyaeu or another string depending on region. The result field contains a model field, which is a json string containing the detailed information about the dps under the properties field. abilityId maps to the id, code and name tell the function of the dp, sometimes they do not match, so the user may be need to be prompted for which is correct after translating the name. typeSpec contains information about the type, range and enum values. type raw means base64, value means integer, bitmap means bitfield.

## Rules for making config files

- The configuration file format is defined in `custom_components/tuya_local/devices/device_config_schema.json` and documented in `custom_components/tuya_local/devices/README.md`.
- Likely a device with the same functionality already exists. Search the `custom_components/tuya_local/devices` folder for a device with the same set of functions. `uv run best_match '${LOCAL_LOG}'` can be helpful for finding the closest match.
- If a device config matches perfectly except for the product details, then an entry can be made under the products section of that config for the user's device instead of creating a new config file.
- If a device config is found that is close, but not perfectly matching, it can be used as a template for a new config. If multiple files are close matches, the most recently added one is likely to be the best quality template to follow.
- To create a unique but concise filename, the format `${BRAND}_${MODEL}_${TYPE}.yaml` is used, where ${BRAND} is the brand as ASCII lower case letters and numbers with spaces and punctuation removed, ${MODEL} is the model name or number as ASCII lower case letters and numbers with spaces and punctuation removed, and ${TYPE} is the type of device as lower case ASCII letters with spaces and punctuation removed. If model is unknown, then `${BRAND}_${TYPE}` can be used.
- If the name chosen by this formula already exists, first check if the dps details are a close match, if there are no conflicts then it may be better to modify the exisiting config to add missing details. If this is done, any added dps must be larked as `optional: true` in case the older variant is missing these.
- If the name chosen already exists and is not a match, append v2 to the ${MODEL} portion of the name. If this also exists, try v3, etc.
- The top level `name` inside the config should be generic, without branding, as other brands of device can often match the same config. Branding should go under `products` only.
- The `products` entry for the device must have an `id`, as determined in the information gathering above. If known, the `manufacturer` and `model` should be filled in. Rarely, model is split into a descriptive `model` and a code `model_id`.
- Higher level entities are preferred when they fit a device's functionality. If the device is a heater, airconditioner or heatpump that both heats and cools, there should be a climate entity, and as much functionality as can be supported by the climate entity should go in there. Water heaters with only heat function should be water_heater entities. Humidifiers and dehumidifiers should be humidifier entities. Air purifiers should generally be fan entities.
- Make use of translation keys where possible instead of explicit names and icons
- Primary functions of a device and most sensors should not have a category. Config entities that are not frequently used should have `category: config`. Sensors and binary_sensors that are not generally useful in dashboards should have `category: diagnostic`.
- Certain patterns are used for commonly encountered functions:
    - child lock functions are implemented as `lock` entities with `translation_key: child_lock`.
    - fault sensors are implemented as `binary_sensor` entities with `class: problem`. When they are bitfields (bitmap in Tuya API), 0 should map to false, and the default mapping is to true. The raw value is available as a `fault_code` attribute on the entity, and if sufficient information is available for human readable descriptions of each fault, then a `description` attribute may be added with mapping of `0` to `ok` and other values to the appropriate human readable description.
- where a suitable class is available for a sensor, and it is the only sensor of that class, no name is necessary. Some classes of sensor have translation keys defined for ${CLASS}_x, these can be used when there are multiple sensors of the same class as:
```yaml
   - entity: sensor
     class: ${CLASS}
     translation_key: ${CLASS}_x
     translation_placeholders:
       x: "${N}"
```
     where ${N} is a number, letter or word uniquely identifying that sensor among the class.
     Where no such `translation_key` exists, a unique `name` is required instead.
     Where one sensor stands out as the main sensor for that class, it can be unnamed and without translation_key, and all the others named or translated as above.

- after creating the new device config, run `uv run duplicates ${CONFIG_FILENAME}`. If any 100% matches are listed, then explain the differences between the configs for the PR message.

## Testing instructions

- Find the CI plan in the .github/workflows folder
- Ignore the .github/workflows/hacs-validate.yml workflow if not running from the main repository at https://github.com/make-all/tuya-local
- run `uv run pytest` to run every test defined for the project
- run `uv run pytest tests/test_device_config.py` to test only yaml file changes or additions
- run `uv run pytest tests/test_translations.py` to test only json file changes or additions
- do not add new tests if only making a yaml or json file change
- add new tests if making a python file change that introduces new functionality
- fix any test or lint failures until the whole test suite passes

## PR instructions

- Please separate 
- Always run `uv run ruff check .`, `uv run ruff check --select -I .`, `uv run ruff format --check .` and `uv run yamllint custom_components/tuya_local/devices` before committing
