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
            if fnmatch(file, "*.json") and file != "en.json":
                yield (file, load_json(join(path, file)))


english = None


def get_english():
    global english
    if english is None:
        translations = join(dirname(root.__file__), "translations", "en.json")
        english = load_json(translations)

    return english


def json_compare_keys(english, json, file, path=""):
    matched = True
    for key in english:
        if key not in json:
            # Issue a warning rather than a failure.
            # This lets us catch all the missing translations at once.
            # Also, contributors shouldn't need to add translations for every language.
            warnings.warn(f"{file} Missing translation for {path}{key}")
            matched = False
        elif isinstance(english[key], dict):
            json_compare_keys(english[key], json[key], file, f"{path}{key}.")
    for key in json:
        if key not in english:
            warnings.warn(f"{file} Extra translation for {path}{key}")
            matched = False

    return matched


def test_missing_translations():
    english = get_english()
    unmatched = []
    for file, json in get_translations():
        if not json_compare_keys(english, json, file):
            unmatched.append(file)
    if unmatched:
        raise AssertionError(f"Inconsistent translations in {', '.join(unmatched)}")


# @pytest.mark.parametrize("device", get_devices())
# def test_device_covered(device):
#     for entity in device.all_entities():
#         if entity.deprecated:
#             subtest_entity_covered(entity)
