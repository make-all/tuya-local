# Instructions for autonomous agents

## Development environment

- This project is a Home Assistant integration.
- The source languages are Python, YAML and JSON
- package management is using `uv`
- Use `uv run ...` to run commands on the project

## Coding standards

- Python files should be checked with `uv run ruff check`, `uv run ruff check --select -I`
- Python files should be formatted consistently with `uv run ruff format`
- YAML files for device configuration should be checked with `uv run yamllint`
- YAML files for device configuration must be located in the custom_components/tuya_local/devices folder
- Python files implementing the HA integration must be located in custom_components/tuya_local and its subfolders, with unit tests in tests and its subfolders.
- JSON files for translations should be located in the custom_components/tuya_local/translations folder.
- Icons should be defined in custom_components/tuya_local/icons.json, and use icons from the material design icons at https://pictogrammers.com/library/mdi/
- Where possible, new devices should use existing translation_keys which are present in custom_components/tuya_local/translations/*.json and custom/components/tuya_local/icons.json
- if new translation_keys are added, they should be generic, not device specific, and translations should be added to all files in custom_components/tuya_local/translations and relevant icons to custom_components/tuya_local/icons.json. Usually it is best to submit additional translations as a separate PR request from new device submissions, as they can involve a lot of rework to existing configs.
- Device and entity names should follow the Home Assistant naming guidelines. Only the first word should be capitalised.
- Try to keep device and entity names concise.
- Top level names should be unbranded and without redundant words like "Smart" or "WiFi".

## Testing instructions

- Find the CI plan in the .github/workflows folder
- Ignore the .github/workflows/hacs-validate.yml workflow if not running from the main repository at https://github.com/make-all/tuya-local
- run `uv run pytest` to run every test defined for the project
- run `uv run pytest tests/test_device_config.py` to test only yaml file changes or additions
- run `uv run pytest tests/test_translations.py` to test only json file changes or additions
- do not add new tests if only making a yaml or json file change
- add new tests if making a python file change that introduces new functionality
- fix any test or lint failures until the whole test suite passes
- tests under `tests/devices` are obsolete, do not add any additional tests here.

## PR instructions

- Always run `uv run ruff check .`, `uv run ruff check --select -I .`, `uv run ruff format --check .` and `uv run yamllint custom_components/tuya_local/devices` before committing
