"""
Config parser for Tuya Local devices.
"""
from fnmatch import fnmatch
import logging
from os import walk
from os.path import join, dirname, splitext
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
        return self._config.get("legacy_type", splitext(self.config)[0])

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

    def _entity_match_analyse(self, entity, keys, matched, dps):
        """
        Determine whether this entity can be a match for the dps
          Args:
            entity - the TuyaEntityConfig to check against
            keys - the unmatched keys for the device
            matched - the matched keys for the device
            dps - the dps values to be matched
        Side Effects:
            Moves items from keys to matched if they match dps
        Return Value:
            True if all dps in entity could be matched to dps, False otherwise
        """
        for d in entity.dps():
            if (d.id not in keys and d.id not in matched) or not _typematch(
                d.type, dps[d.id]
            ):
                return False
            if d.id in keys:
                matched.append(d.id)
                keys.remove(d.id)
        return True

    def match_quality(self, dps):
        """Determine the match quality for the provided dps map."""
        keys = list(dps.keys())
        matched = []
        if "updated_at" in keys:
            keys.remove("updated_at")
        total = len(keys)
        if not self._entity_match_analyse(self.primary_entity, keys, matched, dps):
            return 0

        for e in self.secondary_entities():
            if not self._entity_match_analyse(e, keys, matched, dps):
                return 0

        return round((total - len(keys)) * 100 / total)


class TuyaEntityConfig:
    """Representation of an entity config for a supported entity."""

    def __init__(self, device, config):
        self._device = device
        self._config = config

    @property
    def name(self):
        """The friendly name for this entity."""
        own_name = self._config.get("name")
        if own_name is None:
            return self._device.name
        else:
            return self._device.name + " " + own_name

    @property
    def legacy_class(self):
        """Return the legacy device corresponding to this config."""
        name = self._config.get("legacy_class")
        if name is None:
            return None
        return locate("custom_components.tuya_local" + name)

    @property
    def deprecated(self):
        """Return whether this entitiy is deprecated."""
        return "deprecated" in self._config.keys()

    @property
    def deprecation_message(self):
        """Return a deprecation message for this entity"""
        replacement = self._config.get(
            "deprecated", "nothing, this warning has been raised in error"
        )
        return (
            f"The use of {self.entity} for {self._device.name} is "
            f"deprecated and should be replaced by {replacement}."
        )

    @property
    def entity(self):
        """The entity type of this entity."""
        return self._config["entity"]

    @property
    def device_class(self):
        """The device class of this entity."""
        return self._config.get("class")

    def dps(self):
        """Iterate through the list of dps for this entity."""
        for d in self._config["dps"]:
            yield TuyaDpsConfig(self, d)

    def find_dps(self, name):
        """Find a dps with the specified name."""
        for d in self.dps():
            if d.name == name:
                return d
        return None


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
        return types.get(t)

    @property
    def name(self):
        return self._config["name"]

    def get_value(self, device):
        """Return the value of the dps from the given device."""
        return self._map_from_dps(device.get_property(self.id), device)

    async def async_set_value(self, device, value):
        """Set the value of the dps in the given device to given value."""
        if self.readonly:
            raise TypeError(f"{self.name} is read only")
        if self.invalid:
            raise AttributeError(f"{self.name} cannot be set at this time")

        settings = self.get_values_to_set(device, value)
        await device.async_set_properties(settings)

    @property
    def values(self):
        """Return the possible values a dps can take."""
        if "mapping" not in self._config.keys():
            return None
        val = []
        for m in self._config["mapping"]:
            if "value" in m:
                val.append(m["value"])
            if "conditions" in m:
                for c in m["conditions"]:
                    if "value" in c:
                        val.append(c["value"])

        return list(set(val)) if len(val) > 0 else None

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

    def step(self, device):
        step = 1
        scale = 1
        mapping = self._find_map_for_dps(device.get_property(self.id))
        if mapping is not None:
            step = mapping.get("step", 1)
            scale = mapping.get("scale", 1)
        return step / scale

    @property
    def readonly(self):
        return "readonly" in self._config.keys() and self._config["readonly"] is True

    @property
    def invalid(self):
        return False

    @property
    def hidden(self):
        return "hidden" in self._config.keys() and self._config["hidden"] is True

    def _find_map_for_dps(self, value):
        if "mapping" not in self._config.keys():
            return None
        default = None
        for m in self._config["mapping"]:
            if "dps_val" not in m:
                default = m
            elif str(m["dps_val"]) == str(value):
                return m
        return default

    def _map_from_dps(self, value, device):
        result = value
        mapping = self._find_map_for_dps(value)
        if mapping is not None:
            scale = mapping.get("scale", 1)
            if not isinstance(scale, (int, float)):
                scale = 1
            replaced = "value" in mapping
            result = mapping.get("value", result)
            if "conditions" in mapping:
                cond_dps = (
                    self
                    if "constraint" not in mapping
                    else self._entity.find_dps(mapping["constraint"])
                )
                for c in mapping["conditions"]:
                    if (
                        "dps_val" in c
                        and c["dps_val"] == device.get_property(cond_dps.id)
                        and "value" in c
                    ):
                        result = c["value"]
                        replaced = True

            if scale != 1 and isinstance(result, (int, float)):
                result = result / scale
                replaced = True

            if replaced:
                _LOGGER.debug(
                    "%s: Mapped dps %s value from %s to %s",
                    self._entity._device.name,
                    self.id,
                    value,
                    result,
                )

        return result

    def _find_map_for_value(self, value):
        if "mapping" not in self._config.keys():
            return None
        default = None
        for m in self._config["mapping"]:
            if "dps_val" not in m:
                default = m
            if "value" in m and str(m["value"]) == str(value):
                return m
            if "conditions" in m:
                for c in m["conditions"]:
                    if "value" in c and c["value"] == value:
                        return m
        return default

    def get_values_to_set(self, device, value):
        """Return the dps values that would be set when setting to value"""
        result = value
        dps_map = {}
        mapping = self._find_map_for_value(value)
        if mapping is not None:
            replaced = False
            scale = mapping.get("scale", 1)
            if not isinstance(scale, (int, float)):
                scale = 1
            step = mapping.get("step")
            if not isinstance(step, (int, float)):
                step = None
            if "dps_val" in mapping:
                result = mapping["dps_val"]
                replaced = True
            # Conditions may have side effect of setting another value.
            if "conditions" in mapping and "constraint" in mapping:
                c_dps = self._entity.find_dps(mapping["constraint"])
                for c in mapping["conditions"]:
                    if "value" in c and c["value"] == value:
                        dps_map.update(c_dps.get_values_to_set(device, c["dps_val"]))

            if scale != 1 and isinstance(result, (int, float)):
                _LOGGER.debug(f"Scaling {result} by {scale}")
                result = result * scale
                replaced = True

            if step is not None and isinstance(result, (int, float)):
                _LOGGER.debug(f"Stepping {result} to {step}")
                result = step * round(float(result) / step)
                replaced = True

            if replaced:
                _LOGGER.debug(
                    "%s: Mapped dps %s to %s from %s",
                    self._entity._device.name,
                    self.id,
                    result,
                    value,
                )

        if self.range is not None:
            minimum = self.range["min"]
            maximum = self.range["max"]
            if result < minimum or result > maximum:
                raise ValueError(
                    f"Target {self.name} ({value}) must be between "
                    f"{minimum} and {maximum}"
                )

        if self.type is int:
            _LOGGER.debug(f"Rounding {self.name}")
            result = int(round(result))
        elif self.type is bool:
            result = True if result else False
        elif self.type is float:
            result = float(result)
        elif self.type is str:
            result = str(result)
        dps_map[self.id] = result
        return dps_map


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
