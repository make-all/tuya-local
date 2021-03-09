# Home Assistant Tuya Local component

[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=security_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=ncloc)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=coverage)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)

The `tuya_local` component integrates Goldair WiFi-enabled [heaters](http://www.goldair.co.nz/product-catalogue/heating/wifi-heaters), [dehumidifiers](http://www.goldair.co.nz/product-catalogue/heating/dehumidifiers) and [fans](http://www.goldair.co.nz/product-catalogue/cooling/pedestal-fans/40cm-dc-quiet-fan-with-wifi-and-remote-gcpf315), Kogan WiFi-enabled [heaters](https://www.kogan.com/au/c/smarterhome-range/shop/heating-cooling/) and [plugs](https://www.kogan.com/au/shop/connected-home/smart-plug/), Andersson heaters, Eurom [heaters](https://eurom.nl/en/product-category/heating/wifi-heaters/), Purline [heaters](https://www.purline.es/hoti-m100--ean-8436545097380.htm) and Garden PAC pool [heatpumps](https://www.iot-pool.com/en/products/bomba-de-calor-garden-pac-full-inverter) into Home Assistant, enabling control of setting the following parameters via the UI and the following services:

### Climate devices

**Goldair GPPH Heaters**

- **power** (on/off)
- **mode** (Comfort, Eco, Anti-freeze)
- **target temperature** (`5`-`35` in Comfort mode, `5`-`21` in Eco mode, in °C)
- **power level** (via the swing mode setting because no appropriate HA option exists: `Auto`, `1`-`5`, `Stop`)

Current temperature is also displayed.

**Goldair GPCV Heaters**
- **power** (on/off)
- **mode** (Low, High)
- **target temperature** (`15`-`35` in °C)

Current temperature is also displayed.

**Goldair GECO Heaters**
- **power** (on/off)
- **target temperature** (`15`-`35` in °C)

Current temperature is also displayed.

**Goldair Dehumidifiers**

- **power** (on/off)
- **mode** (Normal, Low, High, Dry clothes, Air clean)
- **target humidity** (`30`-`80`%)

Current temperature is displayed, and current humidity is available as a property. The "tank full" state is available via the **error** attribute, and if you want to you can easily surface this to a top-level entity using a [template sensor](https://www.home-assistant.io/integrations/template/).

**Goldair Fans**

- **power** (on/off)
- **mode** (Normal, Eco, Sleep)
- **fan mode** (`1`-`12`)
- **swing** (on/off)

**Kogan Heaters**

- **power** (on/off)
- **mode** (LOW/HIGH)
- **target temperature** (`16`-`30` in °C)

Current temperature is also displayed.

**Andersson Heaters**

- **power** (on/off)
- **mode** (ANTI-FREEZE/LOW/HIGH)
- **target temperature** (`5`-`35` in °C)

Current temperature is also displayed.

**Eurom Heaters**

- **power** (on/off)
- **target temperature** (`15`-`35` in °C)

Current temperature is also displayed.

**Garden PAC Pool Heatpumps**

- **power** (on/off)
- **mode** (silent/smart)
- **target temperature** (`18`-`45` in °C)

Current temperature is also displayed. Power level, operating mode are available as attributes.

**Purline Hoti M100 Heaters**

- **power** (heat/fan-only/off)
- **mode** (Fan, 1-5, Auto)
- **target temperature** (`16`-`35` in °C)
- **swing** (on/off)

### Additional features

**Light** (Goldair and Purline devices)

- **LED display** (on/off)

**Lock** (Goldair heaters and dehumidifiers)

- **Child lock** (on/off)

**Open Window Detector** (Purline devices)

- **Open Window Detect** (on/off)

### Switch devices

**Kogan Energy monitoring Smart Plug**
- **power** (on/off)
- **current power consumption** (Watts)
- **Additional non-standard attributes**
  - **current current draw** (Amps)
  - **current voltage** (Volts)
  - **timer** (seconds) [provided as read only]

Newer models with a USB socket are also supported.

---

### Device support

Please note, this component is actively tested with the Goldair GPPH (inverter), GPDH420 (dehumidifier), Kogan SmarterHome 1500W Smart Panel Heater and Kogan SmarterHome Energy Monitoring SmartPlug. Theoretically it should also work with GECO, GEPH and GPCV heater devices, and GCPF315 fan and may work with the GPDH440 dehumidifier and any other Goldair heaters, dehumidifiers or fans and Kogan heaters and smartplugs based on the Tuya platform.

GPCV support is based on feedback from @etamtlosz on upstream Issue #27. GECO support is based on work in [KiLLeRRaT/homeassistant-goldair-climate](https://github.com/KiLLeRRaT/homeassistant-goldair-climate) and the feature set from the online manual for these heaters. GEPH heaters appear to be the same as the GECO270, so may also work with this setting.  This heater is almost compatible with the GPCV but without the Low/High mode. 

Support for newer Kogan Smartplugs with USB sockets on them is based on feedback from @botts7 on Issue #2.

A number of other brands of plug seem to match the DPS indexes of either the older or newer Kogan Smartplugs, so it is likely to work with other brands of single energy monitoring smartplug also.

Support for heaters visually matching Andersson GSH 3.2 was added based on information from @awaismun on Issue #5.

Support for Eurom Mon Soleil 600 ceiling heaters was added by @FeikoJoosten. It is possible that this support will also work for other models such as Mon Soleil 610 wall panel heaters, and others in the range.

Support for Purline Hoti M100 heaters and Garden PAC pool heatpumps were added based on information from @Xeovar on Issue #11.

---

## Installation

Installation is via the [Home Assistant Community Store (HACS)](https://hacs.xyz/), which is the best place to get third-party integrations for Home Assistant. Once you have HACS set up, simply follow the [instructions for adding a custom repository](https://hacs.xyz/docs/navigation/settings#custom-repositories) and then the integration will be available to install like any other.

## Configuration

You can easily configure your devices using the Integrations UI at `Home Assistant > Configuration > Integrations > +`. This is the preferred method as things will be unlikely to break as this integration is upgraded. You will need to provide your device's IP address, device ID and local key; the last two can be found using [the instructions below](#finding-your-device-id-and-local-key).

If you would rather configure using yaml, add the following lines to your `configuration.yaml` file (but bear in mind that if the configuration options change your configuration may break until you update it to match the changes):

```yaml
# Example configuration.yaml entry
tuya_local:
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

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Optional)_ The type of Tuya device. `auto` to automatically detect the device type, or if that doesn't work, select from the available options `heater`, `geco_heater` `gpcv_heater`, `dehumidifier`, `fan`, `kogan_heater`, `gsh_heater`, `eurom_heater`, `gardenpac_heatpump`, `purline_m100_heater`  or `kogan_switch`.

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: auto_

#### climate

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliance as a climate device. (not supported for switches)

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: true_

#### display_light

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliance's LED display control as a light (not supported for Kogan, Andersson, Eurom, GECO or GPCV Heaters, or switches).

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: false_

#### child_lock

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliances's child lock as a lock device (not supported for fans, switches, or Andersson ,Eurom, Purline heaters or Garden PAC heatpumps).

&nbsp;&nbsp;&nbsp;&nbsp;_Default value: false_

#### switch

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this device as a switch device (supported only for switches and Purline heaters for the Open Window Detection)

## Heater gotchas

Goldair GPPH heaters have individual target temperatures for their Comfort and Eco modes, whereas Home Assistant only supports a single target temperature. Therefore, when you're in Comfort mode you will set the Comfort temperature (`5`-`35`), and when you're in Eco mode you will set the Eco temperature (`5`-`21`), just like you were using the heater's own control panel. Bear this in mind when writing automations that change the operation mode and set a temperature at the same time: you must change the operation mode _before_ setting the new target temperature, otherwise you will set the current thermostat rather than the new one.

When switching to Anti-freeze mode, the heater will set the current power level to `1` as if you had manually chosen it. When you switch back to other modes, you will no longer be in `Auto` and will have to set it again if this is what you wanted. This could be worked around in code however it would require storing state that may be cleared if HA is restarted and due to this unreliability it's probably best that you just factor it into your automations.

When child lock is enabled, the heater's display will flash with the child lock symbol (`[]`) whenever you change something in HA. This can be confusing because it's the same behaviour as when you try to change something via the heater's own control panel and the change is rejected due to being locked, however rest assured that the changes _are_ taking effect.

When setting the target temperature, different heaters have different behaviour, which you may need to compensate for.  From observation, GPPH heaters allow the temperature to reach 3 degrees higher than the set temperature before turning off, and 1 degree lower before turning on again.  Kogan Heaters on the other hand turn off when the temperature reaches 1 degree over the targetin LOW mode, and turn on again 3 degrees below the target.  To make these heaters act the same in LOW power mode, you need to set the Kogan thermostat 2 degrees higher than the GPPH thermostat.  In HIGH power mode however, they seem to act the same as the GPPH heaters.

## Fan gotchas

In my experience, fans can be a bit flaky. If they become unresponsive, give them about 60 seconds to wake up again.

## Kogan Switch gotchas

While setting this up, I observed after a while that the current and power readings from the switch were returning 0 when there was clearly a load on the switch.  After unplugging and replugging, the switch started returning only dps 1 and 2 (switch status and timer). If HomeAssistant is restarted in that state, the switch detection would fail, however as Home Assistant was left running, it continued to work with no readings for the current, power and voltage.  I unplugged the switch overnight, and in the morning it was working correctly.

## Finding your device ID and local key

You can find these keys the same way as you would for any Tuya local integration. You'll need the Goldair app or the Tuya Tuya Smart app (the Goldair app is just a rebranded Tuya app), then follow these instructions.

- [Instructions for iOS](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)
- [Instructions for Android](https://github.com/codetheweb/tuyapi/blob/cdb4289/docs/SETUP_DEPRECATED.md#capture-https-traffic)

## Next steps

1. Fallback support for a simple switch device using only a boolean dps 1.  As well as covering the failure mode of the Kogan Switch described in Kogan switch gotchas above, it can also cover basic operation of many other devices that use dps 1 for an on/off switch.
2. Config flow improvement to offer only the options available to the detected device, and an indication of which device was detected.
3. The devices need to be generalized so a new subdirectory with source code is not needed to add a new device.  Instead, device descriptors should be in a yaml file, which is referenced by the config.
4. Further config flow improvements to filter the available types to possibilities based on the known dps.  When many device configurations are supported, this will be required, as not all devices will be distinguishable automatically.
5. This component needs specs! Once they're written I'm considering submitting it to the HA team for inclusion in standard installations. Please report any issues and feel free to raise pull requests.
6. This component is partially unit-tested thanks to the upstream project, but there are a few more to complete. Feel free to use existing specs as inspiration and the Sonar Cloud analysis to see where the gaps are.
7. Once unit tests are complete, the next task is to complete the Home Assistant quality checklist before considering submission to the HA team for inclusion in standard installations.

Please report any issues and feel free to raise pull requests.

## Acknowledgements

None of this would have been possible without some foundational discovery work to get me started:

- [nikrolls](https://github.com/nikrolls)'s [homeassistant-goldair-climate](https://github.com/nikrolls/homeassistant-goldair-climate) was the starting point for expanding to non-Goldair devices as well
- [TarxBoy](https://github.com/TarxBoy)'s [investigation using codetheweb/tuyapi](https://github.com/codetheweb/tuyapi/issues/31) to figure out the correlation of the cryptic DPS states 
- [sean6541](https://github.com/sean6541)'s [tuya-homeassistant](https://github.com/sean6541/tuya-homeassistant) library giving an example of integrating Tuya devices with Home Assistant
- [clach04](https://github.com/clach04)'s [python-tuya](https://github.com/clach04/python-tuya) library
- [etamtlosz](https://github.com/etamtlosz) and [KiLLeRRaT](https://github.com/KiLLeRRaT) for their support and dev work towards GECO and GPCV heaters
- [botts7](https://github.com/botts7) for support towards widening Kogan SmartPlug support.
- [awaismun](https://github.com/awaismun) for assistance in supporting Andersson heaters.
- [FeikoJoosten](https://github.com/FeikoJoosten) for development of support for Eurom heaters.
- [Xeovar](https://github.com/Xeovar) for assistance in supporting Purline M100 heaters and Garden PAC pool heatpumps.
