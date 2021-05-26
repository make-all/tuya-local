"""
Config parser for Tuya Local devices.
"""
from fnmatch import fnmatch
import logging
from os import walk
from os.path import join, dirname
from pydoc import locate

from homeassistant.util.yaml import load_yaml

import custom_components.tuya_local.devices as config_dir

_LOGGER = logging.getLogger(__name__)


def _typematch(type, value):
    # Workaround annoying legacy of bool being a subclass of int in Python
    if type is int and isinstance(value, bool):
        return False

    if isinstance(value, type):
        return True
    # Allow values embedded in strings if they can be converted
    # But not for bool, as everything can be converted to bool
    elif isinstance(value, str) and type is not bool:
        try:
            type(value)
            return True
        except ValueError:
            return False
    return False


class TuyaDeviceConfig:
    """Representation of a device config for Tuya Local devices."""

    def __init__(self, fname):
        """Initialize the device config.
        Args:
            fname (string): The filename of the yaml config to load."""
        _CONFIG_DIR = dirname(config_dir.__file__)
        self._fname = fname
        filename = join(_CONFIG_DIR, fname)
        self._config = load_yaml(filename)
        _LOGGER.debug("Loaded device config %s", fname)

    @property
    def name(self):
        """Return the friendly name for this device."""
        return self._config["name"]

    @property
    def config(self):
        """Return the config file associated with this device."""
        return self._fname

    @property
    def legacy_type(self):
        """Return the legacy conf_type associated with this device."""
        return self._config.get("legacy_type", None)

    @property
    def primary_entity(self):
        """Return the primary type of entity for this device."""
        return TuyaEntityConfig(self, self._config["primary_entity"])

    def secondary_entities(self):
        """Iterate through entites for any secondary entites supported."""
        if "secondary_entities" in self._config.keys():
            for conf in self._config["secondary_entities"]:
                yield TuyaEntityConfig(self, conf)

    def matches(self, dps):
        """Determine if this device matches the provided dps map."""
        for d in self.primary_entity.dps():
            if d.id not in dps.keys() or not _typematch(d.type, dps[d.id]):
                return False

        for dev in self.secondary_entities():
            for d in dev.dps():
                if d.id not in dps.keys() or not _typematch(d.type, dps[d.id]):
                    return False
        _LOGGER.debug("Matched config for %s", self.name)
        return True

    def match_quality(self, dps):
        """Determine the match quality for the provided dps map."""
        keys = list(dps.keys())
        total = len(keys)
        for d in self.primary_entity.dps():
            if d.id not in keys or not _typematch(d.type, dps[d.id]):
                return 0
            keys.remove(d.id)

        for dev in self.secondary_entities():
            for d in dev.dps():
                if d.id not in keys or not _typematch(d.type, dps[d.id]):
                    return 0
                keys.remove(d.id)
        return (total - len(keys)) * 100 / total


class TuyaEntityConfig:
    """Representation of an entity config for a supported entity."""

    def __init__(self, device, config):
        self._device = device
        self._config = config

    @property
    def name(self):
        """The friendly name for this entity."""
        return self._config.get("name", self._device.name)

    @property
    def legacy_class(self):
        """Return the legacy device corresponding to this config."""
        name = self._config.get("legacy_class", None)
        if name is None:
            return None
        return locate("custom_components.tuya_local" + name)

    @property
    def entity(self):
        """The entity type of this entity."""
        return self._config["entity"]

    @property
    def device_class(self):
        """The device class of this entity."""
        return self._config.get("class", None)

    def dps(self):
        """Iterate through the list of dps for this entity."""
        for d in self._config["dps"]:
            yield TuyaDpsConfig(self, d)


class TuyaDpsConfig:
    """Representation of a dps config."""

    def __init__(self, entity, config):
        self._entity = entity
        self._config = config

    @property
    def id(self):
        return str(self._config["id"])

    @property
    def type(self):
        t = self._config["type"]
        types = {
            "boolean": bool,
            "integer": int,
            "string": str,
            "float": float,
            "bitfield": int,
        }
        return types.get(t, None)

    @property
    def name(self):
        return self._config["name"]

    def get_value(self, device):
        """Return the value of the dps from the given device."""
        return self.map_from_dps(device.get_property(self.id))

    async def async_set_value(self, device, value):
        """Set the value of the dps in the given device to given value."""
        await device.async_set_property(self.id, self.map_to_dps(value))

    @property
    def values(self):
        """Return the possible values a dps can take."""
        if "mapping" not in self._config.keys():
            return None
        v = []
        for map in self._config["mapping"]:
            if "value" in map:
                v.append(map["value"])
        return v if len(v) > 0 else None

    @property
    def range(self):
        """Return the range for this dps if configured."""
        if (
            "range" in self._config.keys()
            and "min" in self._config["range"].keys()
            and "max" in self._config["range"].keys()
        ):
            return self._config["range"]
        else:
            return None

    @property
    def isreadonly(self):
        return "readonly" in self._config.keys() and self._config["readonly"] is True

    def map_from_dps(self, value):
        result = value
        scale = 1
        if "mapping" in self._config.keys():
            for map in self._config["mapping"]:
                if "value" in map and ("dps_val" not in map or map["dps_val"] == value):
                    result = map["value"]
                    _LOGGER.debug(
                        "%s: Mapped dps %s value from %s to %s",
                        self._entity._device.name,
                        self.id,
                        value,
                        result,
                    )
                if "scale" in map and "value" not in map:
                    scale = map["scale"]
        return (
            result
            if scale == 1 or not isinstance(result, (int, float))
            else result / scale
        )

    def map_to_dps(self, value):
        result = value
        scale = 1
        if "mapping" in self._config.keys():
            for map in self._config["mapping"]:

                if "value" in map and "dps_val" in map and map["value"] == value:
                    result = map["dps_val"]
                    _LOGGER.debug(
                        "%s: Mapped dps %s to %s from %s",
                        self._entity._device.name,
                        self.id,
                        result,
                        value,
                    )
                if "scale" in map and "value" not in map:
                    scale = map["scale"]
        return (
            result
            if scale == 1 or not isinstance(result, (int, float))
            else result * scale
        )


def available_configs():
    """List the available config files."""
    _CONFIG_DIR = dirname(config_dir.__file__)

    for (path, dirs, files) in walk(_CONFIG_DIR):
        for basename in sorted(files):
            if fnmatch(basename, "*.yaml"):
                yield basename


def possible_matches(dps):
    """Return possible matching configs for a given set of dps values."""
    for cfg in available_configs():
        parsed = TuyaDeviceConfig(cfg)
        if parsed.matches(dps):
            yield parsed


def config_for_legacy_use(conf_type):
    """
    Return a config to use with config_type for legacy transition.
    Note: as there are two variants for Kogan Socket, this is not guaranteed
    to be the correct config for the device, so only use it for looking up
    the legacy class during the transition period.
    """
    for cfg in available_configs():
        parsed = TuyaDeviceConfig(cfg)
        if parsed.legacy_type == conf_type:
            return parsed

    return None
