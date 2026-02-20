# Instructions for autonomous agents

## Development environment

- This project is a Home Assistant integration.
- The source languages are Python, YAML and JSON
- Use `pip install -r requirements-dev.txt` to install dependencies

## Coding standards

- Python files should be checked with `ruff check`, `ruff check --select -I`
- Python files should be formatted consistently with `ruff format`
- YAML files should be checked with yamllint
- YAML files should be located in the custom_components/tuya_local/devices folder
- Python files implementing the HA integration should be located in custom_components/tuya_local and its subfolders, with unit tests in tests and its subfolders.
- JSON files for translations should be located in the custom_components/tuya_local/translations folder.
- Icons should be defined in custom_components/tuya_local/icons.json, and use icons from the material design icons at https://pictogrammers.com/library/mdi/
- Where possible, new devices should use existing translation_keys which are present in custom_components/tuya_local/translations/*.json and custom/components/tuya_local/icons.json
- if new translation_keys are added, they should be generic, not device specific, and translations should be added to all files in custom_components/tuya_local/translations and relevant icons to custom_components/tuya_local/icons.json

## Testing instructions

- Find the CI plan in the .github/workflows folder
- Ignore the .github/workflows/hacs-validate.yml workflow if not running from the main repository at https://github.com/make-all/tuya-local
- run `pytest` to run every test defined for the project
- run `pytest tests/test_device_config.py` to test only yaml file changes or additions
- run `pytest tests/test_translations.py` to test only json file changes or additions
- do not add new tests if only making a yaml or json file change
- add new tests if making a python file change that introduces new functionality
- fix any test or lint failures until the whole test suite passes

## PR instructions

- Always run `ruff check .`, `ruff check --select -I .`, `ruff format --check .` and `yamllint custom_components/tuya_local/devices` before committing
