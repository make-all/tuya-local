# Device Configuration Files

This directory contains device configuration files, describing the workings
of supported devices. The files are in YAML format, and describe the mapping
of Tuya DPs (Data Points) to HomeAssistant attributes.

Each Tuya device may correspond to one or more entities in Home Assistant.

## The Top Level

The top level of the device configuration defines the following:

### `name`

The device should be named descriptively with a name the user would recognize.
In general, the brand and model of the device should go under products, and a
generic name for the type of device should go in the top level name.

### `products`

*Optional.*

A list of products that this config applies to. Each product in the list must
have an `id` specified, which corresponds to the product_id from cloud device 
info, or productKey from the local discovery. If these are different, it is
recommended that listings are created for both.

In addition to the id, the `manufacturer`, `model` and `model_id` (if
the model has both a name and a more code like id) can be listed here.
In future the intention is to display these in the Device info panel
for the device. The `name` can also be overridden here with a more
specific name to be used in future in place of the generic name at the
top of the config.

### `entities`

This contains a list of Home Assistant entities providing the functionality
of the device.

The configuration for each entity in the list is detailed in the section below.

## Entity configuration

### `entity`

The Home Assistant entity type being configured. See the **Entity types**
section below for details on specific requirements for each entity type.

### `class`

*Optional.*

For some entity types, a device `class` can be set, for example `switch`
entities can have a class of `outlet`. This may slightly alter the UI
behaviour.
For most entities, it will alter the default icon, and for binary sensors
also the state that off and on values translate to in the UI.

### `translation_key` / `translation_only_key`

*Optional*

A key used to define strings and icons for this entity. If this is used,
the name can be omited and instead defined in the translations files.

`translation_key` will be used to generate IDs when there is no name defined.
If the intention is to have an unnamed entity, or to inherit from class, then
use `translation_only_key` instead (this is mostly useful to retain
backward compatibility where `translation_key` is used to define icons and
attribute strings but not the entity name.

### `translation_placeholders`

*Optional*

A container for placeholders to be used in the translation string. Contents
are a mapping from parameter keys used in the translation files, to actual
values to be used for this entity. If this is specified, then either
translation_key or translation_only_key must be specified with it.

Example:

```
  translation_key: switch_x
  translation_placeholders:
    x: "1"
```

### `category`

*Optional.*

This specifies the `entity category` of the entity. Entities can be categorized
as `config` or `diagnostic` to restrict where they appear automatically in
Home Assistant.

### `name`

*Optional.*

The name associated with this entity can be set here. If no name is
set, it will inherit the name at the top level. This is mostly useful
for overriding the name entities to give more information about the
purpose of the entity, or to differentiate multiple entities of the
same type.

Where possible, `translation_key` should be used instead of an explicit name.

### `mode`

*Optional. For number entities, default="auto", for others, None*

For number entities, this can be used to force `slider` or `box` as the
input method. The default `auto` uses a slider if the range is small enough,
or a box otherwise. It is recommended to let HA decide based on its own logic
which mode to use, and override it in the UI settings rather than forcing
your personal preference on others. But if an entity really does only make
sense with one UI mode, then this is provided to handle those cases.

### `hidden`

*Optional, true/unavailable, default=false*

If `hidden` is `true`, then the entity will be disabled by default.
If `hidden` is `unavailable`, then the entity will be disabled by default if
the entity's `available` dp indicates it is unavailable. This may not work
correctly if the device has not returned data yet when HA checks
for this at startup.

This can be used with advanced config or diagnostic entities that general
users will not be interested in. To use such entities, the user must explicitly
enable them after adding the device to Home Assistant.

### `dps`

This is a list of the definitions for the Tuya DPs associated with
attributes of this entity. There should be one list entry for each
supported DPs reported by the device.

The configuration of DPs entries is detailed in its own section below.


## DPs configuration

### `id`

Every DP must have a numeric ID matching the DP ID in the Tuya protocol.

### `type`

The type of data returned by the Tuya API. Can be one of the following:

 - **string** can contain arbitrary text.
 - **boolean** can contain the values **True** or **False**.
 - **integer** can contain only numbers. Integers can have range set on them, be scaled and steped
 - **bitfield** is a special case of integer, where the bits that make up the value each has individal meaning.
 - **unixtime** is a special case of integer, where the device uses a unix timestamp (seconds since 1970-01-01 00:00), which is converted to a datetime for Home Assistant
 - **base64** is a special case of string, where binary data is base64 encoded. Platforms that use this type will need special handling to make sense of the data.
 - **hex** is a special case of string, where binary data is hex encoded. Platforms that use this type will need special handling to make sense of the data.
 - **json** is a special case of string, where multiple data points are encoded in json format in the string. Platforms that use this type will need special handling to make sense of the data.
 - **utf16b64** is a special case of string, where a UTF-16 string is base64 encoded. This will be decoded into a UTF-8 string so it is readable in Home Assistant.
 - **float** can contain floating point numbers. No known devices use this, but it is supported if needed.

### `name`

The name given to the attribute in Home Assistant. Certain names are used
by the Home Assistant entities for specific purposes. If a name is not
recognized as a standard attribute by the entitiy implementation, the
attribute will be returned as a readonly extra attribute on the entity.
If you need non-standard attributes to be able to be set, you will need
to use an entity for that (typically switch, number or select).

### `sensitive`

*Optional, default false.*

A boolean setting yo mark attributes as containing potentially sensitive
data.  Setting this to true will result in the data being redacted in
device diagnostics output.

### `readonly`

*Optional, default false.*

A boolean setting to mark attributes as readonly. If not specified, the
default is `false`. If set to `true`, the attributes will be reported
to Home Assistant, but attempting to set them will result in an error.
This is only needed in contexts where it would normally be possible to set
the value. If you are creating a sensor entity, or adding an attribute of an
entity which is inherently read-only, then you do not need to specify this.

### `optional`

*Optional, default false.*

A boolean setting to mark attributes as optional. This allows a device to be
matched even if it is not sending the dp at the time when adding a new device.
It can also be used to match a range of devices that have variations in the extra
attributes that are sent.

### `persist`

*Optional, default true.*

Whether to persist the value if the device does not return it on every status
refresh. Some devices don't return every value on every status poll. In most
cases, it is better to remember the previous value, but in some cases the
dp is used to signal an event, so when it is next sent, it should trigger
automations even if it is the same value as previously sent. In that case
the value needs to go to null in between when the device is not sending it.

### `force`

*Optional, default false.*

A boolean setting to mark dps as requiring an explicit update request
to fetch. Many energy monitoring smartplugs require this, without a
explicit request to update them, such plugs will only return monitoring data
rarely or never. Devices can misbehave if this is used on dps that do not
require it. Use this only where needed, and generally only on read-only dps.

### `precision`

*Optional, default None.*

The number of decimals which should be used in the sensor's state when
it's displayed. If unspecified, the Home Assistant will use the native
precision, which is calculated based on the scale of the dp so as to
provide distinct values with as few decimal places as possible. For
example a scale of 3 will result in one decimal place by default,
(values displayed as x.3, x.7 rather than x.33333333 and x.666666) but
you could override that to 2 or 0 by specifying the precision
explicitly.

### `mapping`

*Optional. Must be a list with each item starting with a `- ` (a dash and a space):*
This can be used to define a list of additional rules that modify the DP
to Home Assistant attribute mapping to something other than a one to one
copy.

The rules can range from simple value substitution to complex
relationships involving other attributes.

### `hidden`

*Optional, default false.*
This can be used to define DPs that do not directly expose Home Assistant
attributes. When set to **true**, no attribute will be sent. A `name` should
still be specified and the attribute can be referenced as a `constraint`
from mapping rules on other attributes to implement complex mappings.

An example of use is a climate device, where the Tuya device keeps separate
temperature settings for different Normal and Eco preset modes. The Normal
temperature setting is exposed through the standard `temperature`
Home Assistant attribute on the climate device, but the `eco_temperature`
setting on a different DP is set to hidden. Mapping Rules are used on the
`temperature` attribute to redirect to `eco_temperature` when `preset_mode`
is set to Eco.

### `range`

*Optional, may be required in some contexts, may have defaults in others.*

For integer attributes that are not readonly, a range can be set with `min`
and `max` values that will limit the values that the user can enter in the
Home Assistant UI. This can also be set in a `mapping` or `conditions` block.

### `unit`

*Optional, default="C" for temperature dps on climate devices.*

For temperature dps, some devices will use Fahrenhiet. This needs to be
indicated back to HomeAssistant by defining `unit` as "F". For sensor
entities, see the HomeAssistant developer documentation for the full list
of possible units (C and F are automatically translated to their Unicode
equivalents, other units are currently ASCII so can be easily entered directly).

### `class`

*Optional.*

For sensors, this sets the state class of the sensor (measurement, total
or total_increasing)


### `format`

*Optional.*

For base64 and hex types, this specifies how to decode the binary data (after hex or base64 decoding).
This is a container field, the contents of which should be a list consisting of `name`, `bytes` and `range` fields. `range` is as described above. `bytes` is the number of bytes for the field, which can be `1`, `2`, or `4`. `name` is a name for the field, which will have special handling depending on
the device type.

### `mask`

*Optional.*

For base64 and hex types, this specifies how to extract a single numeric value from the binary data. The value should be a hex bit mask (eg 00FF00 to extract the middle byte of a 3 byte value). Unlike format, this does not require special handling in the entity platform, as only a single value is being extracted.

### `endianness`

*Optional, default="big"*

For base64 and hex types, this specifies the endianess of the data and mask. Could be "big" or "little".

## Mapping Rules

Mapping rules can change the behavior of attributes beyond simple
copying of DP values to attribute values. Rules can be defined
without a dps_val to apply to all values, or a list of rules that
apply to particular dp values can be defined to change only
particular cases. Rules can even depend on the values of other
elements.

### `dps_val`

*Optional, if not provided, the rule is a default that will apply to all
values not covered by their own dps_val rule.*

`dps_val` defines the DP value that each
rule in the list applies to. This can be used to map specific values from the
Tuya protocol into attribute values that have specific meaning in Home
Assistant. For example, climate entities in Home Assistant define modes
"off", "heat", "cool", "heat_cool", "auto" and "dry". But in the Tuya protocol,
a simple heater just has a boolean off/on switch.
A `dps_val` of `null` can be used to specify a value to be assumed when a
dp is not being returned by the device, to avoid None in some locations where
that causes an issue such as entities showing as unavailable. Such a mapping
is one-way, the value will not be mapped back to a null when setting the dp.

### `value`

*Optional.*

This can be used to set the attribute value seen by Home Assistant to something
different than the DP value from the Tuya protocol. Normally it will be used
with `dps_val` to map from one value to another. Without `dps_val` it will
one-way map all otherwise unmapped dps values to the specified value. This
can be useful for a binary_sensor.

### `hidden`

*Optional, default=false*

When set to true, the mapping value is hidden from the list of all values.
This can be used for items that should not be available for selection by the
user but you still want to map for feedback coming from the device. For
example, some devices have a "Manual" mode, which is automatically selected
when adjustments are made to other settings, but should not be available as
an explicit mode for the user to select.

### `available`

*Optional.*

This works the similarly to `hidden` above, but instead of a boolean
value, this should be set to the name of an attribute, which returns a
boolean value, so that the value can be dynamically hidden or shown. A
typical use is where variants of a device use the same config, and
have a flag attribute that indicates whether certain features are
available or not. The mapping will be hidden from the values list when
the referenced attribute is showing `false`, and shown when it is `true`.

### `scale`

*Optional, default=1.*

This can be used in an `integer` dp mapping to scale the values. For example
some climate devices represent the temperature as an integer in tenths of
degrees, and require a scale of 10 to convert them to degrees expected by
Home Assistant. The scale can also be the other way, for a fan with speeds
1, 2 and 3 as DP values, this can be converted to a percentage with a scale
of 0.03.

### `invert`

*Optional, default=False.*

This can be used in an `integer` dp mapping to invert the range. For example,
some cover devices have an opposite idea of which end of the percentage scale open
and closed are from what Home Assistant assumes. To use this mapping option, a range
must also be specified for the dp.

### `step`

*Optional, default=1.*

This can be used in an `integer` dp mapping to make values jump by a specific
step. It can also be set in a conditions block so that the steps change only
under certain conditions. An example is where a value has a range of 0-100, but
only allows settings that are divisible by 10, so a step of 10 would be set.

### `target_range`

*Optional, has `min` and `max` child attributes, like `range`*

A target range is used together with `range` on a numeric value, to
map the value into a new range. Unlike `scale`, this can shift the
value as well as scale it into the new range. Color temperature is a
major use of this, as Tuya devices often use a range of 0 - 100, 0 -
255 or 0 - 1000, and this needs to be mapped to the Kelvin like 2200 -
6500.

This should normally only be used on a default mapping, as the code
that uses this feature often needs to inform HA of the min and max
values for the UI, which may not handle multipe different mappings
across the range.

### `icon`

*Optional. Deprecated since HA 2024.2 (use translation_key and icons.json to define icons)*

This can be used to override the icon. Most useful with a `dps_val` which
indicates a change from normal operating mode, such as "fan-only",
"defrosting", "tank-full" or some error state.

### `icon_priority`

*Optional. Default 10. Lower numbers mean higher priorities. Deprecated, icons should be defined using icons.json and translation_key since HA 2024.2*

When a number of rules on different attributes define `icon` changes, you
may need to control which have priority over the others. For example,
if the device is off, probably it is more important to indicate that than
whether it is in fan-only or heat mode. So in the off/on DP, you might
give a priority of 1 to the off icon, 3 to the on icon, and in the mode DP
you could give a priority of 2 to the fan icon, to make it override the
normal on icon, but not the off icon.
If you don't specify any priorities, the icons will all get the same priority,
so if any overlap exists in the rules, it won't always be predictable which
icon will be displayed.

### `value_redirect`

*Optional.*

When `value_redirect` is set, the value of the attribute and any attempt to
set it will be redirected to the named attribute instead of the current one.

An example of how this can be useful is where a Tuya heater has a dp for the
target temperature in normal mode, and a different dp for the target
temperature is "eco" mode. Depending on the `preset_mode`, you need to use
one or the other. But Home Assistant just has one `temperature` attribute for
setting target temperature, so the mapping needs to be done before passing to
Home Assistant.

### `value_mirror`

*Optional.*

When `value_mirror` is set, the value of the attribute will be redirected to
the current value of the named attribute. Unlike `value_redirect`, this does
not redirect attempts to set the dp to the redirected dp, but when used in
a map, this can make the mapping dynamic.

An example of how this can be useful is where a thermostat can be configured
to control either a heating or cooling device, but it is not expected to
change this setting during operation. Once set up, the hvac_mode dp can
have a mapping that mirrors the value of the configuration dp.

### `invalid`

*Optional, default false.*

Invalid set to true allows an attribute to temporarily be set read-only in
some conditions. Rather than passing requests to set the attribute through
to the Tuya protocol, attempts to set it will throw an error while it meets
the conditions to be `invalid`. It does not make sense to set this at mapping
level, as it would cause a situation where you can set a value then not be
able to unset it. Instead, this should be used with conditions, below, to
make the behaviour dependent on another DP, such as disabling fan speed
control when the preset is in sleep mode (since sleep mode should force low).

### `default`

*Optional, default false.*

Default set to true allows an attribute to be set as the default value.
This is used by some entities when an argument is not provided to a service call
but the attribute is required to be set to function correctly.
An example is the siren entity which uses the tone attribute to turn on and
off the siren, but when turn_on is called without any argument, it needs to
pick a default tone to use to turn on the siren.

### `constraint`

*Optional, always paired with `conditions`. Default if unspecified is the current attribute*

If a rule depends on an attribute other than the current one, then `constraint`
can be used to specify the element that `conditions` applies to. `constraint` can also refer back to the same attribute - this can be useful for specifying conditional mappings, for example to support two different variants of a device in a single config file, where the only difference is the way they represent enum attributes.

### `conditions`

*Optional, usually paired with `constraint.`*

Conditions defines a list of rules that are applied based on the `constraint` attribute. The contents are the same as Mapping Rules, but `dps_val` applies to the attribute specified by `constraint`, and also can be a list of values to match as well rather than a single value. All others act on the current attribute as they would in the mapping. Although conditions are specified within a mapping, they can also contain a `mapping` of their own to override that mapping. These nested mappings are limited to simple `dps_val` to `value` substitutions, as more complex rules would quickly become too complex to manage.

When setting a dp which has conditions attached, the behaviour is slightly different depending on whether the constraint dp is readonly or not.

For non-readonly constraints that specify a single dps_val, the constraint dp will be set along with the target dp so that the first condition with a value matching the target value is met.

For readonly constraints, the condition must match the constraint dp's current value for anything to be set.

**Example**
```yaml
  ...
  name: target_dp
  mapping:
    - dps_val: 1
      constraint: constraint_dp
      conditions:
        - dps_val: a
          value: x
        - dpa_val: c
          value: z
    - dps_val: 2
      constraint: constraint_dp
      conditions:
        - dps_val: b
          value: x
        - dps_val: c
          value: y
```
If `constraint_dp` is not readonly:

| constraint_dp current dps_val | target_dp target value | dps set |
|---|---|---|
| a | x | target_dp: 1, constraint_dp: a |
| a | y | target_dp: 2, constraint_dp: c |
| a | z | target_dp: 1, constraint_dp: c |
| b | x | target_dp: 1, constraint_dp: a |
| b | y | target_dp: 2, constraint_dp: c |
| b | z | target_dp: 1, constraint_dp: c |
| c | x | target_dp: 1, constraint_dp: a |
| c | y | target_dp: 2, constraint_dp: c |
| c | z | target_dp: 1, constraint_dp: c |

If `constraint_dp` is readonly:

| current constraint_dp | target target_dp | dps set |
|---|---|---|
| a | x | target_dp: 1 |
| a | y | - |
| a | z | - |
| b | x | target_dp: 2 |
| b | y | - |
| b | z | - |
| c | x | - |
| c | y | target_dp: 2 |
| c | z | target_dp: 1 |

Note that each condition must specify a `dps_val` to match againt. If you want to specify a default match, do it outside the conditions.

```
    mapping:
      - dps_val: some_value
        value: defaulted
        constraint: other_dp
        conditions:
          - dps_val: other_value
            value: overridden
```


## Generic dps

The following dps may be defined for any entity type. The names should be
avoided for any extra attribute that is not for the listed purpose.

- **available** (optional, string) a dp name that returns a boolean indicating
whether the entity should show as available or not (even when it appears to be
returning valid state). This may be used to disable entities that the device
indicates it does not support, through a feature flag dp. This should only be
used when the device is permanently indicating a missing feature, as HA may
hide the entity if it is marked as unavailable early enough during startup.

## Entity types

Entities have specific mappings of dp names to functions. Any unrecognized dp name is added to the entity as a read-only extra attribute, so can be observed and queried from HA, but if you need to be able to change it, you should split it into its own entity of an appropriate type (number, select, switch for example).

If the type of dp does not match the expected type, a mapping should be provided to convert. Note that "on" and "off" require quotes in yaml, otherwise it they are interpretted as true/false.

Many entity types support a class attribute which may change the UI behaviour, icons etc. See the HA documentation for the entity type to see what is valid (these may expand over time)

### `alarm_control_panel`
- **alarm_state** (required, string) the alarm state, used to report and change the current state of the alarm. Expects values from the set `disarmed`, `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass`, `pending`, `arming`, `disarming`, `triggered`. Other states are allowed for read-only status, but only the armed... and disarmed states are available as commands.
- **trigger** (optional, boolean) used to trigger the alarm remotely for test or panic button etc.

### `binary_sensor`
- **sensor** (required, boolean) the dp to attach to the sensor.

### `button`
- **button** (required, boolean) the dp to attach to the button. Any
read value will be ignored, but the dp is expected to be present for
device detection unless set to optional. A value of true will be sent
for a button press, map this to the desired dps_val if a different
value is required.

### `camera`
- **motion_enable** (optional, boolean) a dp that enables and disables motion detection features built into the camera.
- **record** (optional, boolean) a dp that turns reecording on and off.
- **snapshot** (optional, base64 string) a dp that returns a snapshot image.
from the camera.
- **switch** (optional, boolean) a dp to turn the camera on and off.

**NOTE**: tuya-local does not directly support video streaming from cameras.  Some cameras provide ONVIF or WebRTC compliant streams locally which you can use the relevant integrations to capture, others may be cloud-only.

### `climate`
- **current_temperature** (optional, number) a dp that reports the current temperature.
- **current_humidity** (optional, number) a dp that reports the current humidity (%).
- **fan_mode** (optional, mapping of strings) a dp to control the fan mode if available.
    Any value is allowed, but HA has some standard modes:
    `"on", "off", auto, low, medium, high, top, middle, focus, diffuse`
- **humidity** (optional, number) a dp to control the target humidity if available. (%)
- **hvac_mode** (optional, mapping of strings) a dp to control the mode of the device.
    Possible values are: `"off", cool, heat, heat_cool, auto, dry, fan_only`
- **hvac_action** (optional, string) a dp that reports the current action of the device.
    Possible values are: `"off", idle, cooling, heating, drying, fan, defrosting`
- **preset_mode** (optional, mapping of strings) a dp to control preset modes of the device.
   Any value is allowed, but HA has some standard presets:
    `none, eco, away, boost, comfort, home, sleep, activity`
   There are also some presets defined by this integration for use with various `translation_key`s, see translations/en.json for details.
- **swing_mode** (optional, mapping of strings) a dp to control swing modes of the device.
   Standard values are: `"off", "on", vertical, horizontal, both`, non-standard values can also be used if needed.
- **swing_horizontal_mode** (optional, mapping of strings) a dp to control horizontal swing independently of the vertical swing.
   Standard values are: `"off", "on"`, non-standard values can also be used if needed.
- **temperature** (optional, number) a dp to set the target temperature of the device.
      A unit may be specified as part of the attribute if a temperature_unit dp is not available, if not
      the default unit configured in HA will be used.
- **target_temp_high** (optional, number) a dp to set the upper temperature range of the device.
     This dp should be paired with `target_temp_low`, and is mutually exclusive with `temperature`
- **target_temp_low** (optional, number) a dp to set the lower temperature range of the device.
- **temperature_unit** (optional, string) a dp that specifies the unit the device is configured for.
    Values should be mapped to "C" or "F" (case sensitive) - often the device will use a boolean or
	lower case for this
- **min_temperature** (optional, number) a dp that specifies the minimum temperature that can be set. Some devices provide this, otherwise a fixed range on the temperature dp can be used.
- **max_temperature** (optional, number) a dp that specifies the maximum temperature that can be set.

### `cover`

Either **position**, **action** or **open** should be specified otherwise the cover will always appear in an unknown state.

- **position** (optional, number 0-100): a dp to control the percentage that the cover is open.
    0 means completely close, 100 means completely open.
- **control** (optional, mapping of strings): a dp to control the cover. Mainly useful if **position** cannot be used.
    Valid values are `open, close, stop`
- **action** (optional, string): a dp that reports the current state of the cover.
   Special values are `opening, closing, opened, closed`
- **open** (optional, boolean): a dp that reports if the cover is open. Only used if **position** is not available.
- **tilt_position** (optional, number): a dp to control the tilt opening of the cover (an example is venetian blinds that tilt as well as go up and down). The range will be auto-converted to the 0-100 expected by HA.

### `fan`
- **switch** (optional, boolean): a dp to control the power state of the fan
- **preset_mode** (optional, mapping of strings): a dp to control different modes of the fan.
   Values `"off", low, medium, high` used to be handled specially by HA as deprecated speed aliases. If these are the only "presets", consider mapping them as **speed** values instead, as voice assistants will respond to phrases like "turn the fan up/down" for speed.
- **speed** (optional, number): a dp to control the speed of the fan (%).
    if a range is supplied, it will be automatically scaled to the 0-100 range.
    if a mapping is used for dicrete steps, the values must be mapped within that range.
- **oscillate** (optional, boolean): a dp to control whether the fan will oscillate or not.
- **direction** (optional, string): a dp to control the spin direction of the fan.
   Valid values are `forward, reverse`.

### `humidifier`
Humidifer can also cover dehumidifiers (use class to specify which).

- **switch** (optional, boolean): a dp to control the power state of the fan
- **mode** (optional, mapping of strings): a dp to control preset modes of the device
- **humidity** (optional, number): a dp to control the target humidity of the device
- **current_humidity** (optional, number): a dp to report the current humidity measured by the device
- **action** (optional, string): a dp to report the current action the device is performing. Valid actions are `humidifying`, `drying`, `idle` and `off`

### `lawn_mower`
- **activity** (required, string): a dp to report the current activity of the mower. Valid activities are `mowing`, `paused`, `docked`, `error`, `returning` (from LawnMowerActivities in https://github.com/home-assistant/core/blob/dev/homeassistant/components/lawn_mower/const.py). Any additional activities should be mapped to one of those, and exposed through an extra attribute or sensor entity that shows all the statuses that the mower is reporting.

- **command** (required, string): a dp to send commands to the mower. Recognised commands are `start_mowing`, `pause` and `dock`. Any additional commands should be implemented via a `button` or `select` entity.

### `light`
- **switch** (optional, boolean): a dp to control the on/off state of the light
- **brightness** (optional, number): a dp to control the dimmer if available.  If a range is provided, the value will be automatically scaled into the 0-255 range for HA, so there is no need to provide a scale. If there is a fixed list of mappings, the values should be between 0 (off) and 255 (full brightness). If there is no switch dp, a brightness of 0 will be sent to turn the light off.
- **color_temp** (optional, number): a dp to control the color temperature if available. See `target_range` above for mapping Tuya's range into Kelvin.
- **rgbhsv** (optional, hex): a dp to control the color of the light, using encoded RGB and HSV values. The `format` field names recognized for decoding this field are `r`, `g`, `b`, `h`, `s`, `v`. If both RGB and HSV values are supplied by the light, the HSV will be preferred. Either RGB values or HS values are required. If V is missing, the brightness dp is required.
- **named_color** (optional, string): a dp to control the color of the light, using a list of named colors. This is mutually exclusive with the rgbhsv dp. The list of recognised colors is from the HA COLORS table at https://github.com/home-assistant/core/blob/dev/homeassistant/util/color.py
- **color_mode** (optional, mapping of strings): a dp to control which mode to use if the light supports multiple modes.
    Special values: `white, color_temp, hs, xy, rgb, rgbw, rgbww`, others will be treated as effects,
	Note: only white, color_temp and hs are currently supported, others listed above are reserved and may be implemented in future when the need arises.
    If no `color_mode` dp is available, a single supported color mode will be
    calculated based on which of the above dps are available.
- **effect** (optional, mapping of strings): a dp to control effects / presets supported by the light.
   Note: If the light mixes in color modes in the same dp, `color_mode` should be used instead. If the light contains both a separate dp for effects/scenes/presets and a mix of color_modes and effects (commonly scene and music) in the `color_mode` dp, then a separate select entity should be used for the dedicated dp to ensure the effects from `color_mode` are selectable.

### `lock`

The unlock... dps below are normally integers, but can also be boolean, in which case
no information will be available about which specific credential was used to unlock the lock.

- **lock** (optional, boolean): a dp to control the lock state: true = locked, false = unlocked.
- **lock_state** (optional, boolean): a read-only dp to return the current state of the lock separately from the lock dp (if provided).
- **open** (optional, boolean): a dp to open or close the door or gate controlled by the lock, or if marked readonly to report the open status.
- **unlock_fingerprint** (optional, integer): a dp to identify the fingerprint used to unlock the lock.
- **unlock_password** (optional, integer): a dp to identify the password used to unlock the lock.
- **unlock_temp_pwd** (optional, integer): a dp to identify the temporary password used to unlock the lock.
- **unlock_dynamic_pwd** (optional, integer): a dp to identify the dynamic password used to unlock the lock.
- **unlock_offline_pwd** (optional, integer): a dp to identify the offline password used to unlock the lock.
- **unlock_card** (optional, integer): a dp to identify the card used to unlock the lock.
- **unlock_app** (optional, integer): a dp to identify the app used to unlock the lock.
- **unlock_face** (optional, integer): a dp to identify the face used to unlock the lock.
- **unlock_key** (optional, integer): a dp to identify the key used to unlock the lock.
- **unlock_ble** (optional, integer): a dp to identify the BLE device used to unlock the lock.
- **unlock_voice** (optional, integer): a dp to identify the voice assistant user used to unlock the lock.
- **unlock_ibeacon** (optional, integer): a dp to identify the BLE iBeacon used to unlock the lock.
- **unlock_multi** (optional, integer): a dp to identify the multi-factor user that unlocked the lock.
- **request_unlock** (optional, integer): a dp to signal that a request has been made to unlock, the value should indicate the time remaining for approval.
- **approve_unlock** (optional, boolean): a dp to unlock the lock in response to a request.
- **request_intercom** (optional, integer): a dp to signal that a request has been made via intercom to unlock, the value should indicate the time remaining for approval.
- **approve_intercom** (optional, boolean): a dp to unlock the lock in response to an intercom request.
- **jammed** (optional, boolean): a dp to signal that the lock is jammed.

### `number`
- **value** (required, number): a dp to control the number that is set.
- **unit** (optional, string): a dp that reports the units returned by the number.
    This may be useful for devices that switch between C and F, otherwise a fixed unit attribute on the **value** dp can be used.
- **minimum** (optional, number): a dp that reports the minimum the number can be set to.
    This may be used as an alternative to a range setting on the **value** dp if the range is dynamic
- **maximum** (optional, number): a dp that reports the maximum the number can be set to.
    This may be used as an alternative to a range setting on the **value** dp if the range is dynamic

### `remote`
- **send** (required, accepts a string): a dp to send remote codes.
- **receive** (optional, returns strings): a dp to receive learned commands on. If not supplied, the `remote.learn_command` service call will not be available. 
- **control** (optional, accepts strings `"send_ir"`, `"study"`, `"study_exit"`): a dp to send commands seperately from ir codes. If not supplied, commands will be JSON formatted and sent through the **send** dp.
- **delay** (optional, accepts numbers): a dp to set the delay in ms between buttons when there are multiple in the send string. This is only used when a separate **control** dp is also supplied, otherwise the parameter is included in the JSON sent to the **send** dp.
- **code_type** (optional, accepts integers): a dp to set the type of code being sent. The current implementation only supports type `0`. This is only used when a separate **control** dp is also supplied, otherwise the parameter is included in the JSON sent to the **send** dp.
### `select`
- **option** (required, mapping of strings): a dp to control the option that is selected.

### `sensor`
- **sensor** (required, number or string): a dp that returns the current value of the sensor.
- **unit** (optional, string): a dp that returns the unit returned by the sensor.
    This may be useful for devices that switch between C and F, otherwise a fixed unit attribute on the **sensor** dp can be used.

### `siren`
- **switch** (optional, boolean): a dp to switch the siren on and off (depending on the siren, this may trigger it, or arm it for auto triggering). If this is not used, then the **tone** must be present, and containing an "off" option.
- **tone** (optional, mapping of strings): a dp to report and control the siren tone. This dp is required is there is no **switch**, in which case the value "off" will be used for turning off the siren, and will be filtered from the list of available tones. When the **switch** dp is not used, one value must be marked as `default: true` so that the `turn_on` service with no commands works.
- **volume_level** (optional, float in range 0.0-1.0): a dp to control the volume of the siren (probably needs a scale and step applied, since Tuya devices will probably use an integer, or strings with fixed values).
- **duration** (optional, integer): a dp to control how long the siren will sound for.

### `switch`
- **switch** (required, boolean): a dp to control the switch state.

### `text`
- **value** (required, string): a dp to control the text that is set.
   The value dp of a text entity has a few special attributes.
     - `range` can be supplied to define the `min` and `max` length of the text.
     - if `hidden` is specified as `true`, the mode will be set to `password`, otherwise the mode will be `text`.
     - if the `type` is set to `base64` or `hex`, the `pattern` property of the text entity will be set appropriately. There is currently no way to set an arbitrary pattern.

### `vacuum`
- **status** (required, mapping of strings): a dp to report and control the status of the vacuum.
- **command** (optional, mapping of strings): a dp to control the statuss of the vacuum. If supplied, the status dp is only used to report the state.
    Special values: `return_to_base, clean_spot`, others are sent as general commands
- **locate** (optional, boolean): a dp to trigger a locator beep on the vacuum.
- **power** (optional, boolean): a dp to switch full system power on and off
- **activate** (optional, boolean): a dp to start and pause the vacuum
- **direction_control** (optional, mapping of strings): a dp that is used for directional commands
    These are additional commands that are not part of **status**. They can be sent as general commands from HA.
- **error** (optional, bitfield): a dp that reports error status.
    As this is mapped to a single "fault" state, you could consider separate binary_sensors to report on individual errors

### `valve`
- **valve** (required, boolean or integer): a dp that reports the current state of the valve, and if not readonly, can also be used to set the state.  If a number, it should be a percentage between 0 and 100 indicating how far open the valve is.  If a boolean, it should indicate open (true) or closed (false).

### `water_heater`
- **current_temperature** (optional, number): a dp that reports the current water temperature.

- **operation_mode** (optional, mapping of strings): a dp to report and control the operation mode of the water heater. If `away` is one of the modes, another mode must be marked as `default: true` to that the `away_mode_off` service knows which mode to switch out of away mode to.

- **temperature** (optional, number): a dp to control the target water temperature of the water heater. A unit may be specified as an attribute if the `temperature_unit` dp is not available, otherwise the default of HA's current setting will be used.

- **temperature_unit** (optional, string): a dp that reports the unit the device is configured for.
    Values should be mapped to "C" or "F" (case sensitive) - often the device will use a boolean or	lower case for this

- **min_temperature** (optional, number): a dp that reports the minimum temperature the water heater can be set to, in case this is not a fixed value.

- **max_temperature** (optional, number): a dp that reports the maximum temperature the water heater can be set to, in case this is not a fixed value.

- **away_mode** (optional, boolean): a dp to control whether the water heater is in away mode.

