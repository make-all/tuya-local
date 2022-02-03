# Home Assistant Tuya Local component

[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=security_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=ncloc)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=coverage)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)

This is a Home Assistant add-on to support Wi-fi devices running Tuya
firmware without going via the Tuya cloud.  Using this integration
does not stop your devices from sending status to the Tuya cloud, so
this should not be seen as a security measure, rather it improves
speed and reliability by using local connections, and may unlock some
features of your device, or even unlock whole devices, that are not
supported by the Tuya cloud API.  Currently the focus is mainly on
more complex devices, which are not well supported by other similar
integrations. Simpler devices like switches and lights can be covered
by [rospogrigio/localtuya](https://github.com/rospogrigio/localtuya/),
though some switches are now covered by this integration.

---

## Device support

Please note, this component is actively tested with the Goldair GPPH
(inverter), GPDH420 (dehumidifier), Kogan SmarterHome 1500W Smart
Panel Heater and Kogan SmarterHome Energy Monitoring SmartPlug. Other
devices have been added at user request, and may or may not still be
actively in use by others.

Note that devices sometimes get firmware upgrades, or incompatible
versions are sold under the same model name, so it is possible that
the device will not work despite being listed below.

### Heaters

- Goldair heater models beginning with the code GPPH, GCPV, GECO
- Kogan Wi-Fi Convection Panel heaters - KAHTP and KAWFHTP models
- Andersson GSH heater
- Eurom Mon Soleil 300,600,800, 350,601,720 and 300,450,720 Verre heaters
- Eurom Wall Designheat 2000 heater
- Purline Hoti M100 heater
- Wetair WCH-750 heater
- Kogan Flame effect heater - KAWHMFP20BA model
- Nedis convection heater - WIFIHTPL20F models
- Ecostrad Accent iQ heating panels
- Ecostrad iQ Ceramic radiators

### Air Conditioners / Heatpumps

- ElectriQ 12WMINV
- Tadiran Wind 65/3P
- Fersk Vind 2
- Carson CB PA280
- Kogan 2.6kW portable air conditioner
- Eberg Qubo Q40HD
- Eberg Cooly C35HD

### Pool heaters / heatpumps

- Garden PAC pool heatpump
- Madimack Elite V3 pool heatpump
- Madimack(model unknown) pool heatpump
- Remora pool heatpump
- BWT FI 45 heatpump
- Poolex Silverline and Vertigo heatpump
- these seem to use two common controllers, and many other Pool heatpumps
  will work using the above configurations.
  Report issues if there are any differences in presets or other features,
  or if any of the "unknown" values that are returned as attributes can
  be figured out.

### Thermostats
- Inkbird ITC306A thermostat smartplug
- Inkbird ITC308 thermostat smartplug
- Beca BHP-6000 Room Heat Pump control thermostat
- Beca BHT-6000/8000 Floor Heating thermostat
- Beca BHT-002/3000 Floor Heating thermostat (with external temp sensor)
- Moes BHT-002 thermostat (without external temp sensor)
- Beca BAC-002 thermostat
- Awow/Mi-heat TH213 thermostat (two variants)
- Siswell T29UTW thermostat
- Siswell C16 thermostat _(rebadged as Warmme, Klima and others)_
- Minco MH-1823D thermostat
- Owon PCT513 thermostat
- Beok TR9B thermostat _(rebadged as Vancoo and perhaps others)_
- Hysen HY08WE-2 thermostat
- Nashone MTS-700-WB thermostat smartplug

### Fans
- Goldair GCPF315 fan
- Anko HEGSM40 fan
- Lexy F501 fan
- Deta fan controller
- Arlec Grid Connect Smart Ceiling Fan (with and without light)
- Stirling FS1-40DC Pedestal fan
- Aspen ASP 200 fan
- TMWF02 fan controller

### Air Purifiers
- Renpho RP-AP001S air purifier
- Poiema One air purifier
- Himox H06 Air Purifier

### Dehumidifiers
- Goldair GPDH420 dehumidifier
- ElectriQ CD12PW dehumidifier
- ElectriQ CD12PWv2 dehumidifier
- ElectriQ CD20PRO-LE-V2 dehumidifier
- ElectriQ CD25PRO-LE-V2 dehumidifier
- ElectriQ DESD9LW dehumidifier
- Kogan SmarterHome 7L Desiccant dehumidifier
- JJPro JPD01 dehumidifer
- JJPro JPD02 dehumidifier

### Humidifiers
- Eanons QT-JS2014 Purifying humidifier
- Wetair WAW-H1210LW humidifier

### Kitchen Appliances
- Kogan Glass 1.7L Smart Kettle (not reliably detected)

### Smart Meter/Circuit Breaker
- SmartMCB SMT006 Energy Meter

### SmartPlugs/Wall sockets
- Generic Smartplug with Energy monitoring (older models)
  _confirmed as working with Kogan and Blitzwolf Single Smartplugs_
- Generic Smartplug with Energy monitoring (newer models)
  _confirmed working with Kogan single smartplug with USB and Rillpac smartplugs_
- Generic Smartplug with more advanced energy monitoring
  _confirmed working with CBE smartplugs_
- Mirabella Genio Smart plug with USB
- Grid Connect double outlet with Energy Monitoring, Master and Individual switches and Child Lock.
- DIGOO DG-SP202 dual smartplug with energy monitoring and timers.
- DIGOO DG-SP01 USB smartplug with night light.
- Grid Connect double outlet wall socket
- Woox R4028/DIGOO DG-PS01 3 outlet + USB powerstrip with individual timers.
Other brands may work with the above configurations

- Simple Switch - a switch only, can be a fallback for many other unsupported devices, to allow just power to be switched on/off.
- Simple Switch with Timer - a single switch and timer, will probably work for a lot of smart switches that are not covered by the more advanced configs above.

### Covers
- Simple Garage Door

### Vacuum Cleaners
- Lefant M213 Vacuum Cleaner
- Kyvol E30 Vacuum Cleaner

### Miscellaneous
- Qoto 03 Smart Water Valve / Sprinkler Controller

---

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

Installation is via the [Home Assistant Community Store
(HACS)](https://hacs.xyz/), which is the best place to get third-party
integrations for Home Assistant. Once you have HACS set up, simply
follow the [instructions for adding a custom
repository](https://hacs.xyz/docs/faq/custom_repositories) and then
the integration will be available to install like any other.

## Configuration

You can easily configure your devices using the Integrations configuration UI.

[![Add Integration to your Home Assistant
instance.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tuya_local)

### Stage One

The first stage of configuration is to provide the information needed to
connect to the device.

You will need to provide your device's IP address or hostname, device
ID and local key; the last two can be found using [the instructions
below](#finding-your-device-id-and-local-key).

#### host

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ IP or hostname of the device.

#### device_id

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Device ID retrieved
[as per the instructions below](#finding-your-device-id-and-local-key).

#### local_key

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Local key retrieved
[as per the instructions below](#finding-your-device-id-and-local-key).

At the end of this step, an attempt is made to connect to the device and see if
it returns any data. For tuya protocol version 3.3 devices, success
at this point indicates that all settings you have supplied are correct, but
for protocol version 3.1 devices, the local key is only used for sending
commands to the device, so if your local key is incorrect the setup will
appear to work, and you will not see any problems until you try to control
your device.  Note that each time you pair the device, the local key changes,
so if you obtained the local key using the instructions linked above, then
repaired with your manufacturer's app, then the key will have changed already.

### Stage Two

The second stage of configuration is to select which device you are connecting.
The list of devices offered will be limited to devices which appear to be
at least a partial match to the data returned by the device.

#### type

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Optional)_ The type of Tuya device.
Select from the available options.

If you pick the wrong type, you will need to delete the device and set
it up again.

### Stage Three

The final stage is to choose a name for the device in Home Assistant,
and select which entities you want to enable.  The options availble
will depend on the capabilities of the device you selected in the
previous step.

Usually you will want to accept the defaults at this step.  Entities
are selected by default, unless they are a deprecated alternative way
of controlling the device (such as a climate entity for dehumidifiers
as an alternative to humidifier and fan entities).  If you have
multiple devices of the same type, you may want to change the name to
make it easier to distinguish them.

#### name

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Any unique name for the
device.  This will be used as the base for the entitiy names in Home
Assistant.  Although Home Assistant allows you to change the name
later, it will only change the name used in the UI, not the name of
the entities.

#### (entities)

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ A number of options
will be available for each of the entities exposed by the device.
They will be named for the platform type and an optional name for
the entity as a suffix (eg `climate`, `humidifier`, `lock_child_lock`)
Setting them to True will expose the entity in Home Assistant.

## Offline operation gotchas

Many Tuya devices will stop responding if unable to connect to the Tuya servers for an extended period.  Reportedly, some devices act better offline if DNS as well as TCP connections is blocked.


## Heater gotchas

Goldair GPPH heaters have individual target temperatures for their
Comfort and Eco modes, whereas Home Assistant only supports a single
target temperature. Therefore, when you're in Comfort mode you will
set the Comfort temperature (`5`-`35`), and when you're in Eco mode
you will set the Eco temperature (`5`-`21`), just like you were using
the heater's own control panel. Bear this in mind when writing
automations that change the operation mode and set a temperature at
the same time: you must change the operation mode _before_ setting the
new target temperature, otherwise you will set the current thermostat
rather than the new one.

When switching to Anti-freeze mode, the heater will set the current
power level to `1` as if you had manually chosen it. When you switch
back to other modes, you will no longer be in `Auto` and will have to
set it again if this is what you wanted. This could be worked around
in code however it would require storing state that may be cleared if
HA is restarted and due to this unreliability it's probably best that
you just factor it into your automations.

When child lock is enabled, the heater's display will flash with the
child lock symbol (`[]`) whenever you change something in HA. This can
be confusing because it's the same behaviour as when you try to change
something via the heater's own control panel and the change is
rejected due to being locked, however rest assured that the changes
_are_ taking effect.

When setting the target temperature, different heaters have different
behaviour, which you may need to compensate for.  From observation,
GPPH heaters allow the temperature to reach 3 degrees higher than the
set temperature before turning off, and 1 degree lower before turning
on again.  Kogan Heaters on the other hand turn off when the
temperature reaches 1 degree over the targetin LOW mode, and turn on
again 3 degrees below the target.  To make these heaters act the same
in LOW power mode, you need to set the Kogan thermostat 2 degrees
higher than the GPPH thermostat.  In HIGH power mode however, they
seem to act the same as the GPPH heaters.

The Inkbird thermostat switch does not seem to work for setting
anything.  If you can figure out how to make setting temperatures and
presets work, please leave feedback in Issue #19.

## Fan gotchas

Fans should be configured as `fan` entities, with any auxilary
functions such as panel lighting control, child locks or additional
switches configured as `light`, `lock` or `switch` entities.
Configuration of Goldair fans as `climate` entities is supported for
backward compatibility but is deprecated, and may be removed in
future.

Reportedly, Goldair fans can be a bit flaky. If they become
unresponsive, give them about 60 seconds to wake up again.

Anko fans mostly work, except setting the speed does not seem to
work. If you can figure out how to set the speed through the Tuya
protocol for these devices, please leave feedback on Issue #22.


## Smart Switch gotchas

It has been observed after a while that the current and
power readings from the switch were returning 0 when there was clearly
a load on the switch.  After unplugging and replugging, the switch
started returning only dps 1 and 2 (switch status and timer). If
HomeAssistant is restarted in that state, the switch detection would
fail, however as Home Assistant was left running, it continued to work
with no readings for the current, power and voltage.  I unplugged the
switch overnight, and in the morning it was working correctly.

Cumulative Energy readings seem to be reset whenever the reading is
successfully sent to the server.  This leads to the energy usage never moving
from the minimum reporting level of 0.1kWh, which isn't very useful.
It may be possible to get useful readings by blocking the switch from accessing
the internet, otherwise an integration sensor based on the Power sensor
will need to be set up on the Home Assistant side, and the Energy sensor
ignored.

## Kogan Kettle gotchas

Although these look like simple devices, their behaviour is not
consistant so they are difficult to detect.  Sometimes they are
misdetected as a simple switch, other times they only output the
temperature sensor so are not detected at all.

## Beca thermostat gotchas

These devices support switching between Celcius and Fahrenheit on the control
panel, but do not provide any information over the Tuya local protocol about
which units are selected.  Two configurations for this device are provided,
`beca_bhp6000_thermostat_c` and `beca_bhp6000_thermostat_f`, please select
the appropriate one for the temperature units you use.  If you change the
units on the device control panel, you will need to delete the device from
Home Assistant and set it up again.

## Siswell C19 thermostat gotchas

These support configuration as either heating or cooling controllers, but
only have one output.  The HVAC mode is provided as an indicator of which
mode they are in, but are set to readonly so that you cannot accidentally
switch the thermostat to the wrong mode from HA.

## Humidifiers and dehumidifiers

Humidifiers and Dehumidifiers should be configuured as `humidifier`
entities, probably with `fan` entities as well if the fan speed can
also be controlled, and any other auxilary features such as panel
lighting, child locks or additional switches configured as `light`,
`lock` or `switch` entities.  Configration of Goldair Dehumidifiers
and Eanons Humidifiers as `climate` entities is also supported for
backwards compatibility, but is deprecated and may be removed in
future.  In particular, when humidifiers are represented as `climate`
entities, the running mode will show as `Dry`, as the climate entity
only supports functions commonly found on air conditioners/heatpumps.


## Finding your device ID and local key

You can find these keys the same way as you would for any Tuya local integration. You'll need the Goldair app or the Tuya Tuya Smart app (the Goldair app is just a rebranded Tuya app), then follow these instructions.

- [Instructions for iOS](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)
- [Instructions for Android](https://github.com/codetheweb/tuyapi/blob/cdb4289/docs/SETUP_DEPRECATED.md#capture-https-traffic)

## Next steps

1. This component is mosty unit-tested thanks to the upstream project, but there are a few more to complete. Feel free to use existing specs as inspiration and the Sonar Cloud analysis to see where the gaps are.
2. Once unit tests are complete, the next task is to complete the Home Assistant quality checklist before considering submission to the HA team for inclusion in standard installations.
3. Discovery seems possible with the new tinytuya library, though the steps to get a local key will most likely remain manual.  Discovery also returns a productKey, which might help make the device detection more reliable where different devices use the same dps mapping but different names for the presets for example.

Please report any issues and feel free to raise pull requests.
[Many others](https://github.com/make-all/tuya-local/blob/main/ACKNOWLEDGEMENTS.md) have contributed their help already.


[![BuyMeCoffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jasonrumney)
