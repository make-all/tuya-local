# Device Configuration Files

This directory contains device configuration files, describing the workings
of supported devices. The files are in YAML format, and describe the mapping
of Tuya DPS (Data Point Setting) to HomeAssistant attributes.

Each Tuya device may correspond to one primary entity and any number of
secondary entities in Home Assistant.

## The Top Level

The top level of the device configuration defines the following:

### `name`

The device should be named descriptively with a name the user would recognize,
the brand and model of the device is a good choice.  If a whole family of
devices is supported, a generalization of the model type can be used.
The name should also indicate to the user what type of device it is.

### `legacy_type`

The `legacy_type` is a transitional link back to the device specific
type enumeration that is used in the old device discovery and creation
process. This allows a gradual transition to the new way of handling
devices.  It is required only for devices that exist before the
completion of migratation to generic device classes. It is recommended
that any addition of new devices is deferred until the migration is
complete, as during the transition period it will be neccesary to add
both old device specific classes and device configuration files for
any new devices.

### `primary_entity`

This contains the configuration for one Home Assistant entity which is
considered the main entity for the device. For example, if the device is
a heater, this would be a climate entity.

The configuration for entities is detailed in its own section below.

### `secondary_entities`

//Optional.//

This contains a list of additional Home Assistant entities
providing additional functionality beyond the capabilities of the primary
entity. Examples include lighting control for display panels as a Home
Assistant light entity, child locks as a Home Assistant lock entity,
or additional toggles as Home Assistant switch entities.

The configuration for secondary entities is the same as primary entities,
and is detailed in the section below.

## Entity configuration

### `entity`

The Home Assistant entity type being configured.  Currently supported
types are **climate**, **switch**, **light**, **lock**. Functionality
for these entities is limited to that which has been required for the
devices until now and may need to be extended for new devices.  In
particular, the light and lock entities have only been used for simple
secondary entities, so only basic functionality is implemented.

### `legacy_class`

The `legacy_class` is a transitional link back to the device specific
class that contains the implementation of this device. This will allow
a transition to using device configuration files for discovery and
initialization while the generic entity class implementation is still
in progress. It is required only for devices that exist before the
completion of migratation to generic device classes. It is recommended
that any addition of new devices is deferred until the migration is
complete, as during the transition period it will be neccesary to add
both old device specific classes and device configuration files for
any new devices.

### `dps`

This is a list of the definitions for the Tuya DPS associated with
attributes of this entity.  There should be one list entry for each
supported DPS reported by the device. 

The configuration of DPS entries is detailed in its own section below.

### `name`

//Optional.//

The name associated with this entity can be set here. If no name is set,
it will inherit the name at the top level. This is mostly useful for
overriding the name of secondary entities to give more information
about the purpose of the entity, as the generic type with the top level
name may not be sufficient to describe the function.
 
## DPS configuration
 
### `id`
 
Every DPS must have a numeric ID matching the DPS ID in the Tuya protocol.
 
### `type`
 
The type of data returned by the Tuya API. Can be one of the following:
 
 - **string** can contain arbitrary text.
 - **boolean** can contain the values **True** or **False**.
 - **integer** can contain only numbers (the Tuya protocol typically encloses them in quotes as if they are strings, but integers can have range set on them)
 - **bitfield** is a special case of integer, where the bits that make up the value each has individal meaning.

### `name`

The name given to the attribute in Home Assistant. Certain names are used
by the Home Assistant entities for specific purposes.  If a name is not
recognized as a standard attribute by the entitiy implementation, the
attribute will be returned as a readonly custom attribute on the entity.
If you need non-standard attributes to be able to be set, you will need
to use a secondary entity for that.

### `readonly`

//Optional.//

A boolean setting to mark attributes as readonly. If not specified, the
default is `false`.  If set to `true`, the attributes will be reported
to Home Assistant, but no functionality for setting them will be exposed.

### `mapping`

//Optional.//
This can be used to define a list of additional rules that modify the DPS
to Home Assistant attribute mapping to something other than a one to one
copy. 

The rules can range from simple value substitution to complex
relationships involving other attributes. It can also be used to change
the icon of the entity based on the attribute value. Mapping rules are
defined in their own section below.

### `hidden`

//Optional.//
This can be used to define DPS that do not directly expose Home Assistant
attributes.  When set to **true**, no attribute will be sent. A `name` should
still be specified and the attribute can be referenced as a `constraint`
from mapping rules on other attributes to implement complex mappings.

An example of use is a climate device, where the Tuya device keeps separate
temperature settings for different Normal and Eco preset modes.  The Normal
temperature setting is exposed through the standard `temperature`
Home Assistant attribute on the climate device, but the `eco_temperature`
setting on a different DPS is set to hidden. Mapping Rules are used on the
`temperature` attribute to redirect to `eco_temperature` when `preset_mode`
is set to Eco.

### `range`

//Optional.//

For integer attributes that are not readonly, a range can be set with `min`
and `max` values that will limit the values that the user can enter in the
Home Assistant UI.

## Mapping Rules

Mapping rules can change the behavior of attributes beyond simple copying
of DPS values to attribute values.  Rules can be defined at the top level
of the mapping element to apply to all values, or a list of rules that apply
to particular dps values can be defined to change only particular cases.
Rules can even depend on the values of other elements.

### `dps_val`

//Mandatory for lists, not used at top level.//
When a list of rules is defined, `dps_val` defines the DPS value that each
rule in the list applies to. This can be used to map specific values from the
Tuya protocol into attribute values that have specific meaning in Home
Assistant.  For example, climate entities in Home Assistant define modes
"off", "heat", "cool", "heat_cool", "auto" and "dry". But in the Tuya protocol,
a simple heater just has a boolean off/on switch.  It can also be used to
change the icon when a specific mode is operational.  For example if
a heater device has a fan-only mode, you could change the icon to "mdi:fan"
instead of "mdi:radiator" when in that mode.

### `value`

//Optional.//
This can be used to set the attribute value seen by Home Assistant to something
different than the DPS value from the Tuya protocol.  Normally it will be used
with `dps_val` to map from one value to another. It could also be used at top
level to override all values, but I can't imagine a useful purpose for that.

### `icon`

//Optional.//
This can be used to override the icon.  Most useful with a `dps_val` which
indicates a change from normal operating mode, such as "fan-only",
"defrosting", "tank-full" or some error state.

### `icon_priority`

//Optional. Default 10. Lower numbers mean higher priorities.//
When a number of rules on different attributes define `icon` changes, you
may need to control which have priority over the others.  For example,
if the device is off, probably it is more important to indicate that than
whether it is in fan-only or heat mode.  So in the off/on DPS, you might
give a priority of 1 to the off icon, 3 to the on icon, and in the mode DPS
you could give a priority of 2 to the fan icon, to make it override the
normal on icon, but not the off icon. 
If you don't specify any priorities, the icons will all get the same priority,
so if any overlap exists in the rules, it won't always be predictable which
icon will be displayed.

### `invalid`

//Optional. Boolean, default false.//
Invalid set to true allows an attribute to temporarily be set read-only in
some conditions.  Rather than passing requests to set the attribute through
to the Tuya protocol, attempts to set it will throw an error while it meets
the conditions to be `invalid`.


### `value-redirect`

//Optional.//
When `value-redirect` is set, the value of the attribute and any attempt to
set it will be redirected to the named attribute instead of the current one.

An example of how this can be useful is where a Tuya heater has a dps for the
target temperature in normal mode, and a different dps for the target
temperature is "eco" mode.  Depending on the `preset_mode`, you need to use
one or the other. But Home Assistant just has one `temperature` attribute for
setting target temperature, so the mapping needs to be done before passing to
Home Assistant.


### `constraint`

//Optional. Always paired with `conditions`.//
If a rule depends on an attribute other than the current one, then `constraint`
can be used to specify the element that `conditions` applies to.

### `conditions`

//Optional. Always paired with `constraint.`//
Conditions defines a list of rules that are applied based on the `constraint`
attribute. The contents are the same as Mapping Rules, but `dps_val` applies
to the attribute specified by `constraint`. All others act on the current
attribute as they would in the mapping.  Although conditions are specified
within a mapping, they can also contain a `mapping` of their own to override
that mapping.  Normally such mappings will be simple `dps_val` to `value`
substitutions, as more complex rules will quickly become too complex to
manage.

