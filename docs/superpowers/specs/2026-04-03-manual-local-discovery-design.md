# Manual Local Discovery Design

## Summary

Add a one-time local discovery step to the manual Ledvance Local config flow so the user can pick a discovered Tuya device and have `device_id` and `host` pre-filled before continuing with the existing manual setup form.

The design intentionally reuses `tinytuya` discovery instead of introducing a new background listener or port-level UDP implementation. This keeps the change scoped to config flow UX and avoids touching runtime connection behavior.

## Problem

The current manual flow goes straight to the local setup form and requires the user to already know the device IP address and device ID. The integration only performs local discovery today in the cloud-assisted path, where it uses an already-known device ID to look up the local IP.

This leaves a gap for users who want a fully manual setup path but still want the integration to help them locate devices on the local network.

## Goals

- Add a discovery-first step to the manual config flow.
- List locally discovered devices in a dropdown.
- Let the user pick a discovered device and pre-fill `device_id` and `host`.
- Preserve a manual fallback path when discovery fails or does not find the target device.
- Keep the remainder of the config flow unchanged after the pre-fill step.

## Non-Goals

- No background or long-lived discovery service.
- No runtime IP auto-update or reconnect-on-broadcast behavior.
- No changes to cloud-assisted setup behavior.
- No changes to how the integration connects to a configured device after setup.

## Recommended Approach

Use `tinytuya` local discovery as a one-shot scan during the config flow.

This is preferred over porting `localtuya`'s UDP discovery implementation because:

- the project already depends on `tinytuya`
- the required feature is limited to config-time discovery
- reusing the existing dependency keeps maintenance and risk low

## User Flow

### Manual Entry Path

1. User starts the integration and chooses the manual setup path.
2. Instead of opening the existing `local` form immediately, the flow opens a new `discover_local` step.
3. The integration performs a one-time local scan and shows a dropdown of discovered devices plus a `manual` fallback option.
4. If the user selects a discovered device:
   - `device_id` is pre-filled from the discovery result
   - `host` is pre-filled from the discovery result
   - `protocol_version` is pre-filled if discovery reports one
   - the flow continues to the existing `local` form
5. If the user selects `manual`, the flow continues to the existing `local` form with no discovery defaults.
6. The rest of the flow continues unchanged: connection test, type selection, and final naming.

### Failure and Empty-State Behavior

- If discovery raises an exception, the flow must still allow setup by falling back to the existing `local` form.
- If discovery returns no devices, the flow must still allow setup by offering or directly entering the manual fallback path.
- Discovery must never block the user from completing manual setup.

## Architecture

### Existing Flow

Today `ConfigFlowHandler.async_step_user()` immediately routes to `async_step_local()` because cloud-assisted entry is disabled for now.

The cloud-assisted path separately uses `async_step_search()` and `scan_for_device()` to locate the IP address for a known cloud-selected device.

### New Flow Shape

Add a new config-flow step:

- `async_step_discover_local()`

Update the manual path to become:

- `async_step_user()` -> `async_step_discover_local()` -> `async_step_local()`

The existing `async_step_local()` remains the authoritative place for collecting and validating local connection parameters.

## Data Model

Normalize local discovery output into an internal structure with these fields:

```python
{
    "id": "<device id>",
    "ip": "<ip address>",
    "version": "<protocol version or empty string>",
    "product_key": "<productKey or empty string>",
    "label": "<text shown in the selector>",
}
```

Notes:

- `label` should include the device ID and IP so the UI remains useful even when a friendly name is unavailable.
- `product_key` is not required for the immediate feature but should be preserved if available because it can improve later config matching with minimal extra cost.

## File-Level Changes

### `custom_components/ledvance_local/config_flow.py`

Primary implementation file.

Expected changes:

- add a one-shot local scan helper, e.g. `scan_for_devices()`
- add a new `async_step_discover_local()`
- update `async_step_user()` so the manual path starts with discovery
- store the selected discovery result on the flow instance for use by `async_step_local()`
- keep `async_step_local()` mostly unchanged and only extend its default-value handling

### `custom_components/ledvance_local/translations/*.json`

Add a new config step entry for `discover_local`.

At minimum:

- step title
- step description
- dropdown field label

All translation files must receive the same structural key additions to keep the translation tests passing.

### `tests/test_config_flow.py`

Extend the existing config-flow test suite.

Add tests for:

- the manual path starting at `discover_local` instead of `local`
- selecting a discovered device and seeing `device_id` and `host` pre-filled in `local`
- selecting `manual` and reaching the existing blank `local` form
- empty or failing discovery falling back without breaking the flow
- downstream `local` -> `select_type` -> `choose_entities` behavior remaining intact

### `README.md`

Update the manual setup documentation to mention that the manual path can now attempt local discovery and pre-fill `device_id` and IP address.

## UX Details

The discovery step should present a dropdown with:

- one option per discovered device
- one explicit fallback option for manual entry

Recommended fallback option value:

```text
manual
```

Recommended label shape for discovered devices:

```text
<device_id> - <ip address>
```

If a stable readable name is available from discovery, it may be prefixed, but the UI should not depend on it.

## Error Handling

- Catch discovery exceptions and log them at warning or debug level.
- Do not surface discovery failure as a hard flow error if the user can still continue manually.
- Avoid adding retry loops or background listeners in this change.
- Deduplicate discovered devices by `device_id` before building selector options.

## Testing Strategy

### Unit Tests

Focus on `tests/test_config_flow.py`.

Mock discovery results rather than performing real network scans.

Cover:

- successful discovery with one or more devices
- manual fallback selection
- empty discovery results
- discovery exception handling
- preservation of existing flow behavior after the `local` step

### Existing Validation

Because this change touches Python and translations, the expected validation set is:

- `pytest`
- `pytest tests/test_translations.py`
- `ruff check .`
- `ruff check --select -I .`
- `ruff format --check .`

## Risks

### Discovery API Shape

`tinytuya` discovery output may differ from the shape returned by `find_device()`. The implementation should isolate this in a normalization helper instead of spreading assumptions across the config flow.

### Config Flow Regression

The manual path currently starts directly at `local`, and there are existing tests that assume that. Those tests will need to be updated carefully so the new flow entry point is intentional rather than a regression.

### Translation Drift

Adding a new step key requires synchronized updates across all translation files. Failing to do this will break translation consistency tests.

## Out of Scope Follow-Up Ideas

These are intentionally not part of this design:

- background discovery shared across the integration lifecycle
- notification of newly seen devices
- automatic runtime IP correction based on broadcasts
- product-key driven matching improvements beyond preserving the discovered field in flow state

## Acceptance Criteria

- Starting the manual config path opens a discovery step before the local form.
- The discovery step lists locally found devices and a manual fallback option.
- Selecting a discovered device pre-fills `device_id` and `host` in the local form.
- Selecting the manual fallback still allows the current manual setup flow to proceed.
- If discovery fails or returns no devices, the user can still complete manual setup.
- Existing post-connection flow behavior remains unchanged.
