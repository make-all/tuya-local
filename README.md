# Home Assistant Tuya Local component

[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=security_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=ncloc)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=coverage)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)

This is a Home Assistant add-on to support Wi-fi devices running Tuya firmware without going via the Tuya cloud.  Using this integration does not stop your devices from sending status to the Tuya cloud, so this should not be seen as a security measure, rather it improves speed and reliability by using local connections, and may unlock some features of your device, or even unlock whole devices, that are not supported by the Tuya cloud API.  Currently the focus is mainly on climate devices, which are not well supported by other similar integrations. Simpler devices like switches and lights can be covered by [rospogrigio/localtuya](https://github.com/rospogrigio/localtuya/).

---

### Device support

Please note, this component is actively tested with the Goldair GPPH (inverter), GPDH420 (dehumidifier), Kogan SmarterHome 1500W Smart Panel Heater and Kogan SmarterHome Energy Monitoring SmartPlug. Other devices have been added at user request, and may or may not still be actively in use by others.

Note that devices sometimes get firmware upgrades, or incompatible versions are sold under the same model name, so it is possible that the device will not work despite being listed below.

#### Heaters

- Goldair heater models beginning with the code GPPH, GCPV, GECO.
- Kogan Wi-Fi Convection Panel heaters.
- Andersson GSH heaters.
- Eurom heaters.
- Purline Hoti M100 heaters.

#### Pool heaters

- Garden PAC pool heatpumps.
- Remora pool heatpumps (partially also BWT FI 45, which differs in its presets)

#### Fans
- Goldair GCPF315 fans

#### Dehumidifiers
- Goldair GPDH420 dehumidifiers

#### Humidifiers
- Eanons QT-JS2014 Purifying Humidifer

#### Thermostats
- Inkbird ITC306A thermostat smartplug

#### SmartPlugs
- Kogan Single Smartplug with Energy Monitoring
- Kogan Single Smartplug with Energy Monitoring and USB charging

---

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

Installation is via the [Home Assistant Community Store (HACS)](https://hacs.xyz/), which is the best place to get third-party integrations for Home Assistant. Once you have HACS set up, simply follow the [instructions for adding a custom repository](https://hacs.xyz/docs/faq/custom_repositories) and then the integration will be available to install like any other.

## Configuration

You can easily configure your devices using the Integrations UI at `Home Assistant > Configuration > Integrations > +`. This is the preferred method as the configuration can be migrated as this integration evovles.  You will need to provide your device's IP address, device ID and local key; the last two can be found using [the instructions below](#finding-your-device-id-and-local-key).


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

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Optional)_ The type of Tuya device. `auto` to automatically detect the device type, or if that doesn't work, select from the available options `heater`, `geco_heater` `gpcv_heater`, `dehumidifier`, `fan`, `kogan_heater`, `gsh_heater`, `eurom_heater`, `gardenpac_heatpump`, `purline_m100_heater`  or `kogan_switch`.  Note that the type is likely to change in future to be a configuration file name or product id, as the hardcoded list is a maintenance burden.

#### climate

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliance as a climate device. (supported for heaters, fans, heatpumps, dehumidifiers and humidifiers)

#### display_light

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliance's LED display control as a light (not supported for Kogan, Andersson, Eurom, GECO or GPCV Heaters, or switches).  This is likely to change in future to `light`, to make way for lights which are not secondary lighting on another device.

#### child_lock

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this appliances's child lock as a lock device (not supported for fans, switches, or Andersson ,Eurom, Purline heaters or Garden PAC heatpumps). This is likely to change in future to `lock`, to make way for locks which are not secondary child locks on another device.

#### switch

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this device as a switch device (supported only for switches, Purline heaters for the Open Window Detection and Eanons humidifiers for the UV Sterilzation)

#### humidifier

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this device as a humidifier device (supported only for humidifiers and dehumidifiers)

#### fan

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Whether to surface this device as a fan device (supported for fans, humidifiers and dehumidifiers)

## Heater gotchas

Goldair GPPH heaters have individual target temperatures for their Comfort and Eco modes, whereas Home Assistant only supports a single target temperature. Therefore, when you're in Comfort mode you will set the Comfort temperature (`5`-`35`), and when you're in Eco mode you will set the Eco temperature (`5`-`21`), just like you were using the heater's own control panel. Bear this in mind when writing automations that change the operation mode and set a temperature at the same time: you must change the operation mode _before_ setting the new target temperature, otherwise you will set the current thermostat rather than the new one.

When switching to Anti-freeze mode, the heater will set the current power level to `1` as if you had manually chosen it. When you switch back to other modes, you will no longer be in `Auto` and will have to set it again if this is what you wanted. This could be worked around in code however it would require storing state that may be cleared if HA is restarted and due to this unreliability it's probably best that you just factor it into your automations.

When child lock is enabled, the heater's display will flash with the child lock symbol (`[]`) whenever you change something in HA. This can be confusing because it's the same behaviour as when you try to change something via the heater's own control panel and the change is rejected due to being locked, however rest assured that the changes _are_ taking effect.

When setting the target temperature, different heaters have different behaviour, which you may need to compensate for.  From observation, GPPH heaters allow the temperature to reach 3 degrees higher than the set temperature before turning off, and 1 degree lower before turning on again.  Kogan Heaters on the other hand turn off when the temperature reaches 1 degree over the targetin LOW mode, and turn on again 3 degrees below the target.  To make these heaters act the same in LOW power mode, you need to set the Kogan thermostat 2 degrees higher than the GPPH thermostat.  In HIGH power mode however, they seem to act the same as the GPPH heaters.

## Fan gotchas

In my experience, Goldair fans can be a bit flaky. If they become unresponsive, give them about 60 seconds to wake up again.

## Humidifiers and dehumidifiers

Dehumidifiers can be represented either by the humidifier or the climate entity type. There are advantages and disadvantages to both.  Humidifiers can also be represented by the climate entity type, however the on state will show as "Dry", since the climate component does not have a "Humidify" mode.  The climate component has built in support for temperature and humidity sensors, and fan control, while the humidifier component does not.  The default card for a humidifier component will display and allow adjustment of the target humidity, while the climate card expects to work with temperature.

## Kogan Switch gotchas

While setting this up, I observed after a while that the current and power readings from the switch were returning 0 when there was clearly a load on the switch.  After unplugging and replugging, the switch started returning only dps 1 and 2 (switch status and timer). If HomeAssistant is restarted in that state, the switch detection would fail, however as Home Assistant was left running, it continued to work with no readings for the current, power and voltage.  I unplugged the switch overnight, and in the morning it was working correctly.

## Finding your device ID and local key

You can find these keys the same way as you would for any Tuya local integration. You'll need the Goldair app or the Tuya Tuya Smart app (the Goldair app is just a rebranded Tuya app), then follow these instructions.

- [Instructions for iOS](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)
- [Instructions for Android](https://github.com/codetheweb/tuyapi/blob/cdb4289/docs/SETUP_DEPRECATED.md#capture-https-traffic)

## Next steps

1. Fallback support for a simple switch device using only a boolean dps 1.  As well as covering the failure mode of the Kogan Switch described in Kogan switch gotchas above, it can also cover basic operation of many other devices that use dps 1 for an on/off switch.
2. Config flow improvement to offer only the options available to the detected device, and an indication of which device was detected.
3. Further config flow improvements to filter the available types to possibilities based on the known dps.  When many device configurations are supported, this will be required, as not all devices will be distinguishable automatically.
4. This component needs specs! Once they're written I'm considering submitting it to the HA team for inclusion in standard installations. Please report any issues and feel free to raise pull requests.
5. This component is partially unit-tested thanks to the upstream project, but there are a few more to complete. Feel free to use existing specs as inspiration and the Sonar Cloud analysis to see where the gaps are.
6. Once unit tests are complete, the next task is to complete the Home Assistant quality checklist before considering submission to the HA team for inclusion in standard installations.
7. Discovery seems possible with the new tinytuya library, though the steps to get a local key will most likely remain manual.  Discovery also returns a productKey, which might help make the device detection more reliable where different devices use the same dps mapping but different names for the presets for example.

Please report any issues and feel free to raise pull requests.

## Acknowledgements

None of this would have been possible without some foundational discovery work to get me started:

- [nikrolls](https://github.com/nikrolls)'s [homeassistant-goldair-climate](https://github.com/nikrolls/homeassistant-goldair-climate) was the starting point for expanding to non-Goldair devices as well.
- [TarxBoy](https://github.com/TarxBoy)'s [investigation using codetheweb/tuyapi](https://github.com/codetheweb/tuyapi/issues/31) to figure out the correlation of the cryptic DPS states .
- [sean6541](https://github.com/sean6541)'s [tuya-homeassistant](https://github.com/sean6541/tuya-homeassistant) library giving an example of integrating Tuya devices with Home Assistant.
- [clach04](https://github.com/clach04)'s [python-tuya](https://github.com/clach04/python-tuya) library.
- [jasonacox](https://github.com/jasonacox)'s [tinytuya](https://github.com/jasonacox/tinytuya) library which improves on the original.
- [etamtlosz](https://github.com/etamtlosz) and [KiLLeRRaT](https://github.com/KiLLeRRaT) for their support and dev work towards GECO and GPCV heaters.
- [botts7](https://github.com/botts7) for support towards widening Kogan SmartPlug support.
- [awaismun](https://github.com/awaismun) for assistance in supporting Andersson heaters.
- [FeikoJoosten](https://github.com/FeikoJoosten) for development of support for Eurom heaters.
- [Xeovar](https://github.com/Xeovar) for assistance in supporting Purline M100 heaters and Garden PAC pool heatpumps.
- [paulmfclark](https://github.com/paulmfclark) for assistance in supporting Remora Inverter pool heatpumps, and [cartman10](https://github.com/cartman10) for assistance with BWT FI 45 pool heater which appears to use almost identical Wi-Fi controls.
 - [superman110](https://github.com/superman110) for assistance in supporting Eanons/purenjoy humidifier.
 - [woolmonkey](https://github.com/woolmonkey) for assistance in supporting Inkbird ITC306A Thermostat.
 
[![BuyMeCoffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jasonrumney)
