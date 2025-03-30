"""
Tests for translation files.
"""

import warnings
from fnmatch import fnmatch
from os import walk
from os.path import dirname, join

from homeassistant.util.json import load_json

import custom_components.tuya_local as root


def get_translations():
    translations = join(dirname(root.__file__), "translations")
    for path, dirs, files in walk(translations):
        for file in files:
            if fnmatch(file, "*.json"):
                yield (file, load_json(join(path, file)))


english = None


def get_english():
    global english
    if english is None:
        translations = join(dirname(root.__file__), "translations", "en.json")
        json = load_json(translations)

    return json


def json_compare_keys(english, json, file, path=""):
    for key in english:
        if key not in json:
            # Issue a warning rather than a failure.
            # This lets us catch all the missing translations at once.
            # Also, contributors shouldn't need to add translations for every language.
            warnings.warn(f"{file} Missing translation for {path}{key}")
        elif isinstance(english[key], dict):
            json_compare_keys(english[key], json[key], file, f"{path}{key}.")


def test_missing_translations():
    english = get_english()
    for file, json in get_translations():
        json_compare_keys(english, json, file)


# @pytest.mark.parametrize("device", get_devices())
# def test_device_covered(device):
#     for entity in device.all_entities():
#         if entity.deprecated:
#             subtest_entity_covered(entity)
