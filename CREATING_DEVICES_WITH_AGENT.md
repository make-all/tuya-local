# Procedure for using AI to create new device configs

## Procedure followed by the developer to gather information from the Tuya Cloud API

**Note: these API calls require an authenticated session on the [Tuya IoT
Developer Platform](https://iot.tuya.com) (Cloud > API Explorer). An AI
agent cannot perform them on its own - a human must run them manually and
drop the resulting JSON files in a folder accessible to the agent, named
`<device>.json`, `<device>_dps.json` and optionally `<device>_functions.json`.
Once the files are made available, the agent can read them and take over the
rest of the procedure described below.**

Use ful links:
 - [Tuya IoT Developer Platform](https://iot.tuya.com)
 - [Tuya Cloud Explorer for EU based projects](https://eu.platform.tuya.com/cloud/explorer)

### Get Device Details (`Device Management > Query Device Details` in Api Explorer)

This will allow you to get the details of a specific device using its device ID. You will need to replace `<device_id>` with the actual ID of the device you want to query.
One of the most important field in there is the `local_key`, which is required for local control of the device.

`GET "https://openapi.tuyaeu.com/v2.0/cloud/thing/<device_id>"`

```json
{
  "result": {
    "active_time": 1784320266,
    "bind_space_id": "<bind_space_id>",
    "category": "<category>",
    "create_time": 1784320266,
    "custom_name": "<custom_name>", 
    "icon": "<icon_url>",
    "id": "<device_id>",
    "ip": "<public_ip>",
    "is_online": true,
    "lat": "<latitude>",
    "local_key": "<local_key>",
    "lon": "<longitude>",
    "model": "<model>",
    "name": "<device_name>",
    "product_id": "<product_id>",
    "product_name": "<product_name>",
    "sub": false,
    "time_zone": "<time_zone>",
    "update_time": 1784320266,
    "uuid": "<uuid>"
  },
  "success": true,
  "t": 1784320266,
  "tid": "<transaction_id>"
}
```

### Get Device Properties (`Device Control > Query Properties` in Api Explorer)

This call will allow you to list all the properties (DPs) of a specific device using its device ID. You will need to replace `<device_id>` with the actual ID of the device you want to query.

`GET "https://openapi.tuyaeu.com/v2.0/cloud/thing/<device_id>/shadow/properties"`

```json
{
  "result": {
    "properties": [
      {
        "code": "<property_code>",
        "custom_name": "<custom_name>",
        "dp_id": 20,
        "time": 1784361229256,
        "type": "<property_type>",
        "value": "<property_value>"
      }
    ]
  },
  "success": true,
  "t": 1784379048898,
  "tid": "<transaction_id>"
}
```

### Get Device Functions (`Device Control (Standard Instruction Set) > Get the instruction set of the device` in Api Explorer)

This call will allow you to find possible values for each DPs of a specific device using its device ID. You will need to replace `<device_id>` with the actual ID of the device you want to query.

`GET "https://openapi.tuyaeu.com/v1.0/iot-03/devices/<device_id>/functions"`

```json
{
  "result": {
    "category": "fsd",
    "functions": [
      {
        "code": "<function_code>",
        "desc": "<function_description>",
        "name": "<function_name>",
        "type": "<function_type>",
        "values": "<function_values>"
      }
    ]
  },
  "success": true,
  "t": 1784379313423,
  "tid": "<transaction_id>"
}
```

## Procedure followed by the AI agent to create a new device config

This section documents, step by step, the actual workflow used (with GitHub Copilot)
to turn the 3 raw JSON files above into a working `custom_components/tuya_local/devices/*.yaml`
config. It is meant to help a human or another agent reproduce the process without
re-discovering the same pitfalls.

### 1. Gather the raw data (human task)

This step **must be done by a human**, since it requires an authenticated
session on the Tuya IoT Developer Platform (see the note at the top of this
document) - an AI agent cannot call these endpoints itself.

The human should save the cloud API responses for the device in a folder of
their choice, accessible to the agent:
- `<device>.json` (device details / `local_key` / `product_id`)
- `<device>_dps.json` (current DP values snapshot)
- Optionally `<device>_functions.json`, if the valid range/enum values of a
  DP are needed (the `_dps.json` snapshot only shows the *current* value,
  not the full range of possible values).

Once these files exist, the agent can pick up the task from step 2 onwards,
entirely from these files, without needing any further API access.

### 2. Read the project documentation first

Before writing any YAML, read:
- `AGENTS.md` (coding standards, testing instructions, where files must live)
- `custom_components/tuya_local/devices/README.md` (full reference of every
  field/entity type/mapping rule available in the config format)

### 3. Look for an existing, similar device config to use as a template

Search the `custom_components/tuya_local/devices/` folder for a config with a
similar DP layout (same DP ids/types), even if it's a different brand. Tuya
devices from the same OEM/factory often reuse the exact same DP scheme.
This saves a lot of guessing, especially for `climate` entities (hvac_mode,
mode, fan speed enums, temperature unit, etc.) which have many small
conventions. Use `grep_search` on distinctive DP `code` values (e.g.
`windspeed`, `fan_speed`) or on the `product_id` to check whether the device
is already (partially) supported.

### 4. Draft the YAML config

- Map every DP from the `_dps.json` snapshot to an entity attribute (see the
  README for the full list of recognized attribute names per entity type).
- Any DP that doesn't have a recognized name will automatically show up as a
  **read-only extra attribute** on the entity - this is fine for
  informational DPs (timers, alarms, model variants) that you don't want to
  build dedicated logic for yet. Don't over-engineer on the first pass.
- Mark as `optional: true` any DP that is not expected to be sent by the
  device on every single status poll (timers not currently running, alarm
  bitfields when no alarm is active, etc.). **This is the single most common
  cause of "device not found" issues**: if a DP is declared required but the
  device happens not to report it during the config flow's connection
  attempt, the whole config will fail to match and the device won't show up
  in the dropdown list.
- Don't guess numeric ranges (e.g. fan speed steps) from a single sample
  value if you can avoid it - ask the user to confirm how many discrete
  steps actually exist. Getting this wrong is easy since Tuya's own app can
  mislabel things (see the empirical fan_mode issue below).

### 5. Validate the YAML before ever touching Home Assistant

Run, from the repository root:

```sh
uv run pytest tests/test_device_config.py -q
uv run yamllint custom_components/tuya_local/devices/<your_new_file>.yaml
```

`yamllint` is picky about trailing blank lines at the end of the file -
strip any extra trailing newline if it complains about `too many blank
lines (empty-lines)`.

If `uv` isn't available in the shell, install it first:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```
The first `uv run` will bootstrap a full virtual env (including a
Home Assistant install), which can take a minute or two.

### 6. Real-world testing in Home Assistant, and how to read the logs

Once tests pass, the user tests the config against a live device. This is
where most real issues surface, since config matching only happens **after**
a successful local connection to the device:

- **Connection failures** (`Failed to refresh device state`) are almost
  always caused by: wrong local IP (not the public IP from the cloud
  JSON!), a stale `local_key` (it changes if the device is re-paired), or
  the wrong protocol version. Protocol `auto` doesn't always correctly
  detect the version - if it fails, try explicit `3.3`, then `3.4`, then
  `3.2` one at a time.
- To get detailed logs, enable debug logging either via
  **Settings > Devices & services > Tuya Local > ⋮ > Enable debug logging**,
  or by adding to `configuration.yaml`:
  ```yaml
  logger:
    default: warning
    logs:
      custom_components.tuya_local: debug
      tinytuya: debug
  ```
- Once connected, `custom_components.tuya_local.helpers.device_config` logs,
  for every candidate config file it tries, either a successful match or the
  precise reason it didn't match:
  `Not match for <name>, missing required DPs: [...]` and/or
  `Not match for <name>, DPs have incorrect type: [...]`.
  This is the most useful log line to search for (`grep -n "Not match for"`)
  when a device isn't being recognized - it tells you exactly which DP is
  missing or has a wrong type, so you know exactly what to fix (usually:
  add `optional: true`).
- A log line like `Device matches <config> with quality of 91%` means a
  config almost matched but not perfectly - this is also worth checking, as
  it might indicate the device actually matches a different, existing config
  reasonably well, or that your new config needs a small adjustment.
- The log file can be large (1-2 MB+) and can't always be read directly by
  file tools due to size limits. From a WSL/Linux shell, Windows paths are
  reachable under `/mnt/c/...`, so it's often faster to `grep` for the
  device's `id`/`uuid`/product name or for `Not match for` directly with
  `grep -n` rather than trying to read the whole file.

### 7. Iterate based on the user's empirical observations

Cloud API data only tells you the DP *ids and current values*, not their
real-world meaning. Enum/mapping values in particular should be verified
against actual device behavior, not just names from the app:
in this session, the Pure Blizzard's `windspeed` DP mapping (`low`/`high`)
turned out to be reversed from what the values' names suggested, and it
also turned out the device only has 2 discrete fan speeds, not 3. Always
prefer the user's empirical, hands-on testing over assumptions from DP
naming or the Tuya app's own labels.

### 8. Common mistakes to avoid

- **Don't let a find/replace edit bleed into the wrong file.** When editing
  several very similar sibling configs (e.g. two air conditioners with
  almost identical DP layouts) in the same batch, always re-read each file
  right after editing it to confirm the `products`/`name` section still
  matches the intended device - a bad string replacement can silently copy
  one device's identity into another's file.
- Keep device-specific files one-per-device while iterating (easier to
  debug); only consider merging multiple products into a single shared
  config file once each has been fully validated in production.
