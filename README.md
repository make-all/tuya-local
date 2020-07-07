# Home Assistant Goldair WiFi Climate component

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=nikrolls_homeassistant-goldair-climate&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=nikrolls_homeassistant-goldair-climate)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=nikrolls_homeassistant-goldair-climate&metric=security_rating)](https://sonarcloud.io/dashboard?id=nikrolls_homeassistant-goldair-climate)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=nikrolls_homeassistant-goldair-climate&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=nikrolls_homeassistant-goldair-climate)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=nikrolls_homeassistant-goldair-climate&metric=ncloc)](https://sonarcloud.io/dashboard?id=nikrolls_homeassistant-goldair-climate)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=nikrolls_homeassistant-goldair-climate&metric=coverage)](https://sonarcloud.io/dashboard?id=nikrolls_homeassistant-goldair-climate)

The `goldair_climate` component integrates [Goldair WiFi-enabled heaters](http://www.goldair.co.nz/product-catalogue/heating/wifi-heaters), [WiFi-enabled dehumidifiers](http://www.goldair.co.nz/product-catalogue/heating/dehumidifiers), and [WiFi-enabled fans](http://www.goldair.co.nz/product-catalogue/cooling/pedestal-fans/40cm-dc-quiet-fan-with-wifi-and-remote-gcpf315) into Home Assistant, enabling control of setting the following parameters via the UI and the following services:

**GPPH Heaters**

- **power** (on/off)
- **mode** (Comfort, Eco, Anti-freeze)
- **target temperature** (`5`-`35` in Comfort mode, `5`-`21` in Eco mode, in °C)
- **power level** (via the swing mode setting because no appropriate HA option exists: `Auto`, `1`-`5`, `Stop`)

Current temperature is also displayed.

**GPCV Heaters**
- **power** (on/off)
- **mode** (Low, High)
- **target temperature** (`15`-`35` in °C)

Current temperature is also displayed.

**GECO Heaters**
- **power** (on/off)
- **target temperature** (`15`-`35` in °C)

Current temperature is also displayed.

**Dehumudifiers**

- **power** (on/off)
- **mode** (Normal, Low, High, Dry clothes, Air clean)
- **target humidity** (`30`-`80`%)

Current temperature is displayed, and current humidity is available as a property. The "tank full" state is available via the **error** attribute, and if you want to you can easily surface this to a top-level entity using a [template sensor](https://www.home-assistant.io/integrations/template/).

**Fans**

- **power** (on/off)
- **mode** (Normal, Eco, Sleep)
- **fan mode** (`1`-`12`)
- **swing** (on/off)

**Light**

- **LED display** (on/off)

**Lock** (heaters and dehumidifiers)

- **Child lock** (on/off)

There was previously a sensor option, however this is easily achieved using a [template sensor](https://www.home-assistant.io/integrations/template/) and therefore is no longer supported.

---

### Device support

Please note, this component is actively tested with the Goldair GPPH (inverter), GPDH420 (dehumidifier), and GCPF315 fan, and community-tested with GECO,and GPCV heater devices. It may work with the GPDH440 dehumidifier, GEPH heater, and other heaters, dehumidifiers or fans based on the Tuya platform.

GPCV support is based on feedback from etamtlosz on Issue #27. GECO support is based on work in KiLLeRRaT/homeassistant-goldair-climate and the feature set from the online manual for these heaters. GEPH heaters appear to be the same as the GECO270, so may also work with this setting. This heater is almost compatible with the GPCV but without the Low/High mode.

---

## Installation

Installation is via the [Home Assistant Community Store (HACS)](https://hacs.xyz/), which is the best place to get third-party integrations for Home Assistant. Once you have HACS set up, simply [search the `Integrations` section](https://hacs.xyz/docs/basic/getting_started) for Goldair.

## Configuration

You can easily configure your devices using the Integrations UI at `Home Assistant > Configuration > Integrations > +`. This is the preferred method as things will be unlikely to break as this integration is upgraded. You will need to provide your device's IP address, device ID and local key; the last two can be found using [the instructions below](#finding-your-device-id-and-local-key).

If you would rather configure using yaml, add the following lines to your `configuration.yaml` file (but bear in mind that if the configuration options change your configuration may break until you update it to match the changes):

```yaml
# Example configuration.yaml entry
goldair_climate:
  - name: My heater
    host: 1.2.3.4
    device_id: <your device id>
    local_key: <your local key>
```

### Configuration variables

#### name

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Any unique name for the device; required because the Tuya API doesn't provide the one you set in the app.

#### host

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ IP or hostname of the device.

#### device_id

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Device ID retrieved
[as per the instructions below](#finding-your-device-id-and-local-key).

#### local_key

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Local key retrieved
[as per the instructions below](#finding-your-device-id-and-local-key).

#### type

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Optional)_ The type of Goldair device. `auto` to automatically detect the device type, or if that doesn't work, select from the available options `heater`, `gpcv_heater`, `geco_heater`, `dehumidifier` or `fan`.

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: auto_

#### climate

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliance as a climate device.

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: true_

#### display_light

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliance's LED display control as a light (not supported for GPCV or GECO heaters).

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: false_

#### child_lock

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliances's child lock as a lock device (not supported for fans).

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: false_

## Heater gotchas

Goldair GPPH heaters have individual target temperatures for their Comfort and Eco modes, whereas Home Assistant only supports a single target temperature. Therefore, when you're in Comfort mode you will set the Comfort temperature (`5`-`35`), and when you're in Eco mode you will set the Eco temperature (`5`-`21`), just like you were using the heater's own control panel. Bear this in mind when writing automations that change the operation mode and set a temperature at the same time: you must change the operation mode _before_ setting the new target temperature, otherwise you will set the current thermostat rather than the new one.

When switching to Anti-freeze mode, the heater will set the current power level to `1` as if you had manually chosen it. When you switch back to other modes, you will no longer be in `Auto` and will have to set it again if this is what you wanted. This could be worked around in code however it would require storing state that may be cleared if HA is restarted and due to this unreliability it's probably best that you just factor it into your automations.

When child lock is enabled, the heater's display will flash with the child lock symbol (`[]`) whenever you change something in HA. This can be confusing because it's the same behaviour as when you try to change something via the heater's own control panel and the change is rejected due to being locked, however rest assured that the changes _are_ taking effect.

## Fan gotchas

In my experience, fans can be a bit flaky. If they become unresponsive, give them about 60 seconds to wake up again.

## Finding your device ID and local key

You can find these keys the same way as you would for any Tuya local integration. You'll need the Goldair app or the Tuya Tuya Smart app (the Goldair app is just a rebranded Tuya app), then follow these instructions.

- [Instructions for iOS](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)
- [Instructions for Android](https://github.com/codetheweb/tuyapi/blob/cdb4289/docs/SETUP_DEPRECATED.md#capture-https-traffic)

You're looking for `uuid` (this is the device ID) and the `localKey` values.

## Next steps

This component is mostly unit-tested, but there are a few more to complete. Feel free to use existing specs as inspiration and the Sonar Cloud analysis to see where the gaps are.

Once unit tests are complete, the next task is to complete the Home Assistant quality checklist before considering submission to the HA team for inclusion in standard installations.

Please report any issues and feel free to raise pull requests.

## Acknowledgements

None of this would have been possible without some foundational discovery work to get me started:

- [TarxBoy](https://github.com/TarxBoy)'s [investigation using codetheweb/tuyapi](https://github.com/codetheweb/tuyapi/issues/31) to figure out the correlation of the cryptic DPS states
- [sean6541](https://github.com/sean6541)'s [tuya-homeassistant](https://github.com/sean6541/tuya-homeassistant) library giving an example of integrating Tuya devices with Home Assistant
- [clach04](https://github.com/clach04)'s [python-tuya](https://github.com/clach04/python-tuya) library
- [make-all](https://github.com/etamtlosz), [etamtlosz](https://github.com/etamtlosz) and [KiLLeRRaT](https://github.com/KiLLeRRaT) for their support and dev work towards GECO and GPCV heaters