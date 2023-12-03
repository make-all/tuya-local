"""
Config parser for Tuya Local devices.
"""
import logging
from base64 import b64decode, b64encode
from collections.abc import Sequence
from datetime import datetime
from fnmatch import fnmatch
from numbers import Number
from os import walk
from os.path import dirname, exists, join, splitext

from homeassistant.util import slugify
from homeassistant.util.yaml import load_yaml

import custom_components.tuya_local.devices as config_dir

_LOGGER = logging.getLogger(__name__)


def _typematch(vtype, value):
    # Workaround annoying legacy of bool being a subclass of int in Python
    if vtype is int and isinstance(value, bool):
        return False

    # Allow integers to pass as floats.
    if vtype is float and isinstance(value, Number):
        return True

    if isinstance(value, vtype):
        return True
    # Allow values embedded in strings if they can be converted
    # But not for bool, as everything can be converted to bool
    elif isinstance(value, str) and vtype is not bool:
        try:
            vtype(value)
            return True
        except ValueError:
            return False
    return False


def _scale_range(r, s):
    "Scale range r by factor s"
    if s == 1:
        return r
    return {"min": r["min"] / s, "max": r["max"] / s}


_unsigned_fmts = {
    1: "B",
    2: "H",
    3: "3s",
    4: "I",
}

_signed_fmts = {
    1: "b",
    2: "h",
    3: "3s",
    4: "i",
}


def _bytes_to_fmt(bytes, signed=False):
    """Convert a byte count to an unpack format."""
    fmt = _signed_fmts if signed else _unsigned_fmts

    if bytes in fmt:
        return fmt[bytes]
    else:
        return f"{bytes}s"


def _equal_or_in(value1, values2):
    """Return true if value1 is the same as values2, or appears in values2."""
    if not isinstance(values2, str) and isinstance(values2, Sequence):
        return value1 in values2
    else:
        return value1 == values2


def _remove_duplicates(seq):
    """Remove dulicates from seq, maintaining order."""
    if not seq:
        return []
    seen = set()
    adder = seen.add
    return [x for x in seq if not (x in seen or adder(x))]


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
    def config_type(self):
        """Return the config type associated with this device."""
        return splitext(self._fname)[0]

    @property
    def legacy_type(self):
        """Return the legacy conf_type associated with this device."""
        return self._config.get("legacy_type", self.config_type)

    @property
    def primary_entity(self):
        """Return the primary type of entity for this device."""
        return TuyaEntityConfig(
            self,
            self._config["primary_entity"],
            primary=True,
        )

    def secondary_entities(self):
        """Iterate through entites for any secondary entites supported."""
        for conf in self._config.get("secondary_entities", {}):
            yield TuyaEntityConfig(self, conf)

    def matches(self, dps):
        required_dps = self._get_required_dps()

        missing_dps = [dp for dp in required_dps if dp.id not in dps.keys()]
        if len(missing_dps) > 0:
            _LOGGER.debug(
                "Not match for %s, missing required DPs: %s",
                self.name,
                [{dp.id: dp.type.__name__} for dp in missing_dps],
            )

        incorrect_type_dps = [
            dp
            for dp in self._get_all_dps()
            if dp.id in dps.keys() and not _typematch(dp.type, dps[dp.id])
        ]
        if len(incorrect_type_dps) > 0:
            _LOGGER.debug(
                "Not match for %s, DPs have incorrect type: %s",
                self.name,
                [{dp.id: dp.type.__name__} for dp in incorrect_type_dps],
            )

        return len(missing_dps) == 0 and len(incorrect_type_dps) == 0

    def _get_all_dps(self):
        all_dps_list = [d for d in self.primary_entity.dps()]
        all_dps_list += [d for dev in self.secondary_entities() for d in dev.dps()]
        return all_dps_list

    def _get_required_dps(self):
        required_dps_list = [d for d in self._get_all_dps() if not d.optional]
        return required_dps_list

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
        all_dp = keys + matched
        for d in entity.dps():
            if (d.id not in all_dp and not d.optional) or (
                d.id in all_dp and not _typematch(d.type, dps[d.id])
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
        if not self._entity_match_analyse(
            self.primary_entity,
            keys,
            matched,
            dps,
        ):
            return 0

        for e in self.secondary_entities():
            if not self._entity_match_analyse(e, keys, matched, dps):
                return 0

        return round((total - len(keys)) * 100 / total)


class TuyaEntityConfig:
    """Representation of an entity config for a supported entity."""

    def __init__(self, device, config, primary=False):
        self._device = device
        self._config = config
        self._is_primary = primary

    @property
    def name(self):
        """The friendly name for this entity."""
        return self._config.get("name")

    @property
    def translation_key(self):
        """The translation key for this entity."""
        return self._config.get("translation_key", self.device_class)

    def unique_id(self, device_uid):
        """Return a suitable unique_id for this entity."""
        return f"{device_uid}-{slugify(self.config_id)}"

    @property
    def entity_category(self):
        return self._config.get("category")

    @property
    def deprecated(self):
        """Return whether this entity is deprecated."""
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
    def config_id(self):
        """The identifier for this entity in the config."""
        own_name = self._config.get("name", self.device_class)
        if own_name:
            return f"{self.entity}_{slugify(own_name)}"

        return self.entity

    @property
    def device_class(self):
        """The device class of this entity."""
        return self._config.get("class")

    def icon(self, device):
        """Return the icon for this device, with state as given."""
        icon = self._config.get("icon", None)
        priority = self._config.get("icon_priority", 100)

        for d in self.dps():
            rule = d.icon_rule(device)
            if rule and rule["priority"] < priority:
                icon = rule["icon"]
                priority = rule["priority"]
        return icon

    @property
    def mode(self):
        """Return the mode (used by Number entities)."""
        return self._config.get("mode")

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
        self.stringify = False

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
            "json": str,
            "base64": str,
            "hex": str,
            "unixtime": int,
        }
        return types.get(t)

    @property
    def rawtype(self):
        return self._config["type"]

    @property
    def name(self):
        return self._config["name"]

    @property
    def optional(self):
        return self._config.get("optional", False)

    @property
    def persist(self):
        return self._config.get("persist", True)

    @property
    def force(self):
        return self._config.get("force", False)

    @property
    def format(self):
        fmt = self._config.get("format")
        if fmt:
            unpack_fmt = ">"
            ranges = []
            names = []
            for f in fmt:
                name = f.get("name")
                b = f.get("bytes", 1)
                r = f.get("range")
                if r:
                    mn = r.get("min")
                    mx = r.get("max")
                else:
                    mn = 0
                    mx = 256**b - 1

                unpack_fmt = unpack_fmt + _bytes_to_fmt(b, mn < 0)
                ranges.append({"min": mn, "max": mx})
                names.append(name)
            _LOGGER.debug("format of %s found", unpack_fmt)
            return {"format": unpack_fmt, "ranges": ranges, "names": names}

        return None

    def mask(self, device):
        mapping = self._find_map_for_dps(device.get_property(self.id))
        if mapping:
            mask = mapping.get("mask")
            if mask:
                return int(mask, 16)

    def endianness(self, device):
        mapping = self._find_map_for_dps(device.get_property(self.id))
        if mapping:
            endianness = mapping.get("endianness")
            if endianness:
                return endianness
        return "big"

    def get_value(self, device):
        """Return the value of the dps from the given device."""
        mask = self.mask(device)
        bytevalue = self.decoded_value(device)
        if mask and isinstance(bytevalue, bytes):
            value = int.from_bytes(bytevalue, self.endianness(device))
            scale = mask & (1 + ~mask)
            return self._map_from_dps((value & mask) // scale, device)
        else:
            return self._map_from_dps(device.get_property(self.id), device)

    def decoded_value(self, device):
        v = self._map_from_dps(device.get_property(self.id), device)
        if self.rawtype == "hex" and isinstance(v, str):
            try:
                return bytes.fromhex(v)
            except ValueError:
                _LOGGER.warning(
                    "%s sent invalid hex '%s' for %s",
                    device.name,
                    v,
                    self.name,
                )
                return None

        elif self.rawtype == "base64" and isinstance(v, str):
            try:
                return b64decode(v)
            except ValueError:
                _LOGGER.warning(
                    "%s sent invalid base64 '%s' for %s",
                    device.name,
                    v,
                    self.name,
                )
                return None
        else:
            return v

    def encode_value(self, v):
        if self.rawtype == "hex":
            return v.hex()
        elif self.rawtype == "base64":
            return b64encode(v).decode("utf-8")
        elif self.rawtype == "unixtime" and isinstance(v, datetime):
            return v.timestamp()
        else:
            return v

    def _match(self, matchdata, value):
        """Return true val1 matches val2"""
        if self.rawtype == "bitfield" and matchdata:
            try:
                return (int(value) & int(matchdata)) != 0
            except (TypeError, ValueError):
                return False
        else:
            return str(value) == str(matchdata)

    async def async_set_value(self, device, value):
        """Set the value of the dps in the given device to given value."""
        if self.readonly:
            raise TypeError(f"{self.name} is read only")
        if self.invalid_for(value, device):
            raise AttributeError(f"{self.name} cannot be set at this time")
        settings = self.get_values_to_set(device, value)
        await device.async_set_properties(settings)

    def values(self, device):
        """Return the possible values a dps can take."""
        if "mapping" not in self._config.keys():
            _LOGGER.debug(
                "No mapping for dpid %s (%s), unable to determine valid values",
                self.id,
                self.name,
            )
            return []
        val = []
        for m in self._config["mapping"]:
            if "value" in m and not m.get("hidden", False):
                val.append(m["value"])
            # If there is mirroring without override, include mirrored values
            elif "value_mirror" in m:
                r_dps = self._entity.find_dps(m["value_mirror"])
                val = val + r_dps.values(device)
            for c in m.get("conditions", {}):
                if "value" in c and not c.get("hidden", False):
                    val.append(c["value"])
                elif "value_mirror" in c:
                    r_dps = self._entity.find_dps(c["value_mirror"])
                    val = val + r_dps.values(device)

            cond = self._active_condition(m, device)
            if cond and "mapping" in cond:
                _LOGGER.debug("Considering conditional mappings")
                c_val = []
                for m2 in cond["mapping"]:
                    if "value" in m2 and not m2.get("hidden", False):
                        c_val.append(m2["value"])
                    elif "value_mirror" in m:
                        r_dps = self._entity.find_dps(m["value_mirror"])
                        c_val = c_val + r_dps.values(device)
                # if given, the conditional mapping is an override
                if c_val:
                    _LOGGER.debug(
                        "Overriding %s values %s with %s",
                        self.name,
                        val,
                        c_val,
                    )
                    val = c_val
                    break
        _LOGGER.debug("%s values: %s", self.name, val)
        return _remove_duplicates(val)

    @property
    def default(self):
        """Return the default value for a dp."""
        if "mapping" not in self._config.keys():
            _LOGGER.debug(
                "No mapping for %s, unable to determine default value",
                self.name,
            )
            return None
        for m in self._config["mapping"]:
            if m.get("default", False):
                return m.get("value", m.get("dps_val", None))
            for c in m.get("conditions", {}):
                if c.get("default", False):
                    return c.get("value", m.get("value", m.get("dps_val", None)))

    def range(self, device, scaled=True):
        """Return the range for this dps if configured."""
        scale = self.scale(device) if scaled else 1
        mapping = self._find_map_for_dps(device.get_property(self.id))
        r = self._config.get("range")
        if mapping:
            _LOGGER.debug("Considering mapping for range of %s", self.name)
            cond = self._active_condition(mapping, device)
            if cond:
                r = cond.get("range", r)

        if r and "min" in r and "max" in r:
            return _scale_range(r, scale)
        else:
            return None

    def scale(self, device):
        scale = 1
        mapping = self._find_map_for_dps(device.get_property(self.id))
        if mapping:
            scale = mapping.get("scale", 1)
            cond = self._active_condition(mapping, device)
            if cond:
                scale = cond.get("scale", scale)
        return scale

    def precision(self, device):
        if self.type is int:
            scale = self.scale(device)
            precision = 0
            while scale > 1.0:
                scale /= 10.0
                precision += 1
            return precision

    @property
    def suggested_display_precision(self):
        return self._config.get("precision")

    def step(self, device, scaled=True):
        step = 1
        scale = self.scale(device) if scaled else 1
        mapping = self._find_map_for_dps(device.get_property(self.id))
        if mapping:
            _LOGGER.debug("Considering mapping for step of %s", self.name)
            step = mapping.get("step", 1)

            cond = self._active_condition(mapping, device)
            if cond:
                constraint = mapping.get("constraint", self.name)
                _LOGGER.debug("Considering condition on %s", constraint)
                step = cond.get("step", step)
        if step != 1 or scale != 1:
            _LOGGER.debug(
                "Step for %s is %s with scale %s",
                self.name,
                step,
                scale,
            )
        return step / scale if scaled else step

    @property
    def readonly(self):
        return self._config.get("readonly", False)

    def invalid_for(self, value, device):
        mapping = self._find_map_for_value(value, device)
        if mapping:
            cond = self._active_condition(mapping, device)
            if cond:
                return cond.get("invalid", False)
        return False

    @property
    def hidden(self):
        return self._config.get("hidden", False)

    @property
    def unit(self):
        return self._config.get("unit")

    @property
    def state_class(self):
        """The state class of this measurement."""
        return self._config.get("class")

    def _find_map_for_dps(self, value):
        default = None
        for m in self._config.get("mapping", {}):
            if "dps_val" not in m:
                default = m
            elif self._match(m["dps_val"], value):
                return m
        return default

    def _correct_type(self, result):
        """Convert value to the correct type for this dp."""
        if self.type is int:
            _LOGGER.debug("Rounding %s", self.name)
            result = int(round(result))
        elif self.type is bool:
            result = True if result else False
        elif self.type is float:
            result = float(result)
        elif self.type is str:
            result = str(result)

        if self.stringify:
            result = str(result)

        return result

    def _map_from_dps(self, val, device):
        if val is not None and self.type is not str and isinstance(val, str):
            try:
                val = self.type(val)
                self.stringify = True
            except ValueError:
                self.stringify = False
        else:
            self.stringify = False

        result = val
        scale = self.scale(device)

        mapping = self._find_map_for_dps(val)
        if mapping:
            invert = mapping.get("invert", False)
            redirect = mapping.get("value_redirect")
            mirror = mapping.get("value_mirror")
            replaced = "value" in mapping
            result = mapping.get("value", result)
            target_range = mapping.get("target_range")

            cond = self._active_condition(mapping, device)
            if cond:
                if cond.get("invalid", False):
                    return None
                replaced = replaced or "value" in cond
                result = cond.get("value", result)
                redirect = cond.get("value_redirect", redirect)
                mirror = cond.get("value_mirror", mirror)
                target_range = cond.get("target_range", target_range)

                for m in cond.get("mapping", {}):
                    if str(m.get("dps_val")) == str(result):
                        replaced = "value" in m
                        result = m.get("value", result)

            if redirect:
                _LOGGER.debug("Redirecting %s to %s", self.name, redirect)
                r_dps = self._entity.find_dps(redirect)
                return r_dps.get_value(device)
            if mirror:
                r_dps = self._entity.find_dps(mirror)
                return r_dps.get_value(device)

            if invert and isinstance(result, Number):
                r = self._config.get("range")
                if r and "min" in r and "max" in r:
                    result = -1 * result + r["min"] + r["max"]
                    replaced = True

            if target_range and isinstance(result, Number):
                r = self._config.get("range")
                if r and "max" in r and "max" in target_range:
                    from_min = r.get("min", 0)
                    from_max = r["max"]
                    to_min = target_range.get("min", 0)
                    to_max = target_range["max"]
                    result = to_min + (
                        (result - from_min) * (to_max - to_min) / (from_max - from_min)
                    )
                    replaced = True

            if scale != 1 and isinstance(result, Number):
                result = result / scale
                replaced = True

            if self.rawtype == "unixtime" and isinstance(result, int):
                try:
                    result = datetime.fromtimestamp(result)
                    replaced = True
                except:
                    _LOGGER.warning("Invalid timestamp %d", result)

            if replaced:
                _LOGGER.debug(
                    "%s: Mapped dps %s value from %s to %s",
                    self._entity._device.name,
                    self.id,
                    val,
                    result,
                )

        return result

    def _find_map_for_value(self, value, device):
        default = None
        nearest = None
        distance = float("inf")
        for m in self._config.get("mapping", {}):
            if "dps_val" not in m:
                default = m
            # The following avoids further matching on the above case
            # and in the null mapping case, which is intended to be
            # a one-way map to prevent the entity showing as unavailable
            # when no value is being reported by the device.
            if m.get("dps_val") is None:
                continue
            if "value" in m and str(m["value"]) == str(value):
                return m
            if (
                "value" in m
                and isinstance(m["value"], Number)
                and isinstance(value, Number)
            ):
                d = abs(m["value"] - value)
                if d < distance:
                    distance = d
                    nearest = m

            if "value" not in m and "value_mirror" in m:
                r_dps = self._entity.find_dps(m["value_mirror"])
                if str(r_dps.get_value(device)) == str(value):
                    return m

            for c in m.get("conditions", {}):
                if "value" in c and str(c["value"]) == str(value):
                    c_dp = self._entity.find_dps(m.get("constraint", self.name))
                    # only consider the condition a match if we can change
                    # the dp to match, or it already matches
                    if (c_dp.id != self.id and not c_dp.readonly) or (
                        _equal_or_in(
                            device.get_property(c_dp.id),
                            c.get("dps_val"),
                        )
                    ):
                        return m
                if "value" not in c and "value_mirror" in c:
                    r_dps = self._entity.find_dps(c["value_mirror"])
                    if str(r_dps.get_value(device)) == str(value):
                        return m
        if nearest:
            return nearest
        return default

    def _active_condition(self, mapping, device, value=None):
        constraint = mapping.get("constraint", self.name)
        conditions = mapping.get("conditions")
        c_match = None
        if constraint and conditions:
            c_dps = self._entity.find_dps(constraint)
            # base64 and hex have to be decoded
            c_val = (
                None
                if c_dps is None
                else (
                    c_dps.get_value(device)
                    if c_dps.rawtype == "base64" or c_dps.rawtype == "hex"
                    else device.get_property(c_dps.id)
                )
            )
            for cond in conditions:
                if c_val is not None and (_equal_or_in(c_val, cond.get("dps_val"))):
                    c_match = cond
                # Case where matching None, need extra checks to ensure we
                # are not just defaulting and it is really a match
                elif (
                    c_val is None
                    and c_dps is not None
                    and "dps_val" in cond
                    and cond.get("dps_val") is None
                ):
                    c_match = cond
                # when changing, another condition may become active
                # return that if it exists over a current condition
                if value is not None and value == cond.get("value"):
                    return cond

        return c_match

    def get_values_to_set(self, device, value):
        """Return the dps values that would be set when setting to value"""
        result = value
        dps_map = {}
        if self.readonly:
            return dps_map

        mapping = self._find_map_for_value(value, device)
        scale = self.scale(device)
        mask = None
        if mapping:
            replaced = False
            redirect = mapping.get("value_redirect")
            invert = mapping.get("invert", False)
            mask = mapping.get("mask")
            endianness = mapping.get("endianness", "big")
            target_range = mapping.get("target_range")
            step = mapping.get("step")
            if not isinstance(step, Number):
                step = None
            if "dps_val" in mapping and not mapping.get("hidden", False):
                result = mapping["dps_val"]
                replaced = True
            # Conditions may have side effect of setting another value.
            cond = self._active_condition(mapping, device, value)
            if cond:
                cval = cond.get("value")
                if cval is None:
                    r_dps = cond.get("value_mirror")
                    if r_dps:
                        cval = self._entity.find_dps(r_dps).get_value(device)

                if cval == value:
                    c_dps = self._entity.find_dps(mapping.get("constraint", self.name))
                    cond_dpsval = cond.get("dps_val")
                    single_match = isinstance(cond_dpsval, str) or (
                        not isinstance(cond_dpsval, Sequence)
                    )
                    if c_dps.id != self.id and single_match:
                        c_val = c_dps._map_from_dps(
                            cond.get("dps_val", device.get_property(c_dps.id)),
                            device,
                        )
                        dps_map.update(c_dps.get_values_to_set(device, c_val))

                # Allow simple conditional mapping overrides
                for m in cond.get("mapping", {}):
                    if m.get("value") == value and not m.get("hidden", False):
                        result = m.get("dps_val", result)

                step = cond.get("step", step)
                redirect = cond.get("value_redirect", redirect)
                target_range = cond.get("target_range", target_range)

            if redirect:
                _LOGGER.debug("Redirecting %s to %s", self.name, redirect)
                r_dps = self._entity.find_dps(redirect)
                return r_dps.get_values_to_set(device, value)

            if scale != 1 and isinstance(result, Number):
                _LOGGER.debug("Scaling %s by %s", result, scale)
                result = result * scale
                remap = self._find_map_for_value(result, device)
                if (
                    remap
                    and "dps_val" in remap
                    and "dps_val" not in mapping
                    and not remap.get("hidden", False)
                ):
                    result = remap["dps_val"]
                replaced = True

            if target_range and isinstance(result, Number):
                r = self._config.get("range")
                if r and "max" in r and "max" in target_range:
                    from_min = target_range.get("min", 0)
                    from_max = target_range["max"]
                    to_min = r.get("min", 0)
                    to_max = r["max"]
                    result = to_min + (
                        (result - from_min) * (to_max - to_min) / (from_max - from_min)
                    )
                    replaced = True

            if invert:
                r = self._config.get("range")
                if r and "min" in r and "max" in r:
                    result = -1 * result + r["min"] + r["max"]
                    replaced = True

            if step and isinstance(result, Number):
                _LOGGER.debug("Stepping %s to %s", result, step)
                result = step * round(float(result) / step)
                remap = self._find_map_for_value(result, device)
                if (
                    remap
                    and "dps_val" in remap
                    and "dps_val" not in mapping
                    and not remap.get("hidden", False)
                ):
                    result = remap["dps_val"]
                replaced = True

            if replaced:
                _LOGGER.debug(
                    "%s: Mapped dps %s to %s from %s",
                    self._entity._device.name,
                    self.id,
                    result,
                    value,
                )

        r = self.range(device, scaled=False)
        if r and isinstance(result, Number):
            mn = r["min"]
            mx = r["max"]
            if round(result) < mn or round(result) > mx:
                # Output scaled values in the error message
                r = self.range(device, scaled=True)
                mn = r["min"]
                mx = r["max"]
                raise ValueError(f"{self.name} ({value}) must be between {mn} and {mx}")

        if mask and isinstance(result, Number):
            # mask is in hex, 2 digits/characters per byte
            length = int(len(mask) / 2)
            # Convert to int
            mask = int(mask, 16)
            mask_scale = mask & (1 + ~mask)
            current_value = int.from_bytes(self.decoded_value(device), endianness)
            result = (current_value & ~mask) | (mask & int(result * mask_scale))
            result = self.encode_value(result.to_bytes(length, endianness))

        dps_map[self.id] = self._correct_type(result)
        return dps_map

    def icon_rule(self, device):
        mapping = self._find_map_for_dps(device.get_property(self.id))
        icon = None
        priority = 100
        if mapping:
            icon = mapping.get("icon", icon)
            priority = mapping.get("icon_priority", 10 if icon else 100)
            cond = self._active_condition(mapping, device)
            if cond and cond.get("icon_priority", 10) < priority:
                icon = cond.get("icon", icon)
                priority = cond.get("icon_priority", 10 if icon else 100)

        return {"priority": priority, "icon": icon}


def available_configs():
    """List the available config files."""
    _CONFIG_DIR = dirname(config_dir.__file__)

    for path, dirs, files in walk(_CONFIG_DIR):
        for basename in sorted(files):
            if fnmatch(basename, "*.yaml"):
                yield basename


def possible_matches(dps):
    """Return possible matching configs for a given set of dps values."""
    for cfg in available_configs():
        parsed = TuyaDeviceConfig(cfg)
        try:
            if parsed.matches(dps):
                yield parsed
        except TypeError:
            _LOGGER.error("Parse error in %s", cfg)


def get_config(conf_type):
    """
    Return a config to use with config_type.
    """
    _CONFIG_DIR = dirname(config_dir.__file__)
    fname = conf_type + ".yaml"
    fpath = join(_CONFIG_DIR, fname)
    if exists(fpath):
        return TuyaDeviceConfig(fname)
    else:
        return config_for_legacy_use(conf_type)


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
