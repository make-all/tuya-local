# Home Assistant Tuya Local component

<<<<<<< HEAD
Fork of [make-all/tuya-local](https://github.com/make-all/tuya-local) with changes to simple blinds.
=======
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=security_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=make-all_tuya-local) [![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=ncloc)](https://sonarcloud.io/dashboard?id=make-all_tuya-local) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=make-all_tuya-local&metric=coverage)](https://sonarcloud.io/dashboard?id=make-all_tuya-local)

Please report any [issues](https://github.com/make-all/tuya-local/issues) and feel free to raise [pull requests](https://github.com/make-all/tuya-local/pulls).
[Many others](https://github.com/make-all/tuya-local/blob/main/ACKNOWLEDGEMENTS.md) have contributed their help already.

[![BuyMeCoffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jasonrumney)

This is a Home Assistant integration to support devices running Tuya
firmware without going via the Tuya cloud.  Devices are supported
over WiFi, other technologies need a Tuya gateway device (Zigbee
devices will work with other Zigbee gateways, but not via this
integration).

Note that many Tuya devices seem to support only one local connection.
If you have connection issues when using this integration, ensure that
other integrations offering local Tuya connections are not configured
to use the same device, mobile applications on devices on the local
network are closed, and no other software is trying to connect locally
to your Tuya devices.

Using this integration does not stop your devices from sending status
to the Tuya cloud, so this should not be seen as a security measure,
rather it improves speed and reliability by using local connections,
and may unlock some features of your device, or even unlock whole
devices, that are not supported by the Tuya cloud API.

A similar but unrelated integration is
[rospogrigio/localtuya](https://github.com/rospogrigio/localtuya/), if
your device is not supported by this integration, you may find it
easier to set up using that as an alternative.


---

## Device support

Note that devices sometimes get firmware upgrades, or incompatible
versions are sold under the same model name, so it is possible that
the device will not work despite being listed.

Battery powered devices such as door and window sensors, smoke alarms
etc which do not use a hub will be impossible to support locally, due
to the power management that they need to do to get acceptable battery
life.

Hubs are currently supported, but with limitations.  Each connection
to a sub device uses a separate network connection, but like other
Tuya devices, hubs are usually limited in the number of connections
they can handle, with typical limits being 1 or 3, depending on the specific
Tuya module they are using.  This severely limits the number of sub devices
that can be connected through this integration.

Tuya Zigbee devices are usually standard zigbee devices, so as an
alternative to this integration with a Tuya hub, you can use a
supported Zigbee USB stick or Wifi hub with
[ZHA](https://www.home-assistant.io/integrations/zha/#compatible-hardware)
or [Zigbee2MQTT](https://www.zigbee2mqtt.io/guide/adapters/).

Tuya Bluetooth devices can be supported directly by the
[tuya_ble](https://github.com/PlusPlus-ua/ha_tuya_ble/) integration.

Tuya IR hubs that expose general IR remotes as sub devices usually
expose them as one way devices (send only).  Due to the way this
integration does device detection based on the dps returned by the
device, it is not currently able to detect such devices at all.  Some
specialised IR hubs for air conditioner remote controls do work, as
they try to emulate a fully smart air conditioner using internal memory
of what settings are currently set, and internal temperature and humidity
sensors.

A list of currently supported devices can be found in the [DEVICES.md](https://github.com/make-all/tuya-local/blob/main/DEVICES.md) file.

Documentation on building a device configuration file is in [/custom_components/tuya_local/devices/README.md](https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/README.md)

If your device is not listed, you can find the information required to add a configuration for it in the following locations:

1. When attempting to add the device, if it is not supported, you will either get a message saying the device cannot be recognised at all, or you will be offered a list of devices (maybe a list of length 1) that are partial matches, often simple switch is among them.  You can cancel the process at this point, and look in the Home Assistant log - there should be a message there containing the current data points (dps) returned by the device.
2. If you have signed up for [iot.tuya.com](https://iot.tuya.com/) to get your local key, you should also have access to the API Explorer under "Cloud". Under "Device Control" there is a function called "Query Things Data Model", which returns the dp_id in addition to range information that is needed for integer and enum data types.
3. By following the method described at the link below, you can find information for all the data points supported by your device, including those not listed by the API explorer method above and those that are only returned under specific conditions. Ignore the requirement for a Tuya Zigbee gateway, that is for Zigbee devices, and this integration does not currently support devices connected via a gateway, but the non-Zigbee/gateway specific parts of the procedure apply also to WiFi devices.

https://www.zigbee2mqtt.io/advanced/support-new-devices/03_find_tuya_data_points.html

If you file an issue to request support for a new device, please include the following information:

1. Identification of the device, such as model and brand name.
2. As much information on the datapoints you can gather using the above methods.
3. If manuals or webpages are available online, links to those help understand how to interpret the technical info above - even if they are not in English automatic translations can help, or information in them may help to identify identical devices sold under other brands in other countries that do have English or more detailed information available.

If you submit a pull request, please understand that the config file naming and details of the configuration may get modified before release - for example if your name was too generic, I may rename it to a more specific name, or conversely if the device appears to be generic and sold under many brands, I may change the brand specific name to something more general.  So it may be necessary to remove and re-add your device once it has been integrated into a release.

---

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Installation is easiest via the [Home Assistant Community Store
(HACS)](https://hacs.xyz/), which is the best place to get third-party
integrations for Home Assistant. Once you have HACS set up, simply click the button below (requires My Homeassistant configured) or
follow the [instructions for adding a custom
repository](https://hacs.xyz/docs/faq/custom_repositories) and then
the integration will be available to install like any other.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=make-all&repository=tuya-local&category=integration)

## Configuration

After installing, you can easily configure your devices using the Integrations configuration UI.  Go to Settings / Devices & Services and press the Add Integration button, or click the shortcut button below (requires My Homeassistant configured).

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


#### protocol_version

&nbsp;&nbsp;&nbsp;&nbsp;_(string or float) (Required)_ Valid options are "auto", 3.1, 3.2, 3.3, 3.4.  If you aren't sure, choose "auto", but some 3.2 and maybe 3.4 devices may be misdetected as 3.3 (or vice-versa), so if your device does not seem to respond to commands reliably, try selecting between those protocol versions.

At the end of this step, an attempt is made to connect to the device and see if
it returns any data. For tuya protocol version 3.1 devices, the local key is
only used for sending commands to the device, so if your local key is
incorrect the setup will appear to work, and you will not see any problems
until you try to control your device.  For more recent Tuya protocol versions,
the local key is used to decrypt received data as well, so an incorrect key
will be detected at this step and cause an immediate failure.  Note that each
time you pair the device, the local key changes, so if you obtained the
local key using the instructions below, then re-paired with your
manufacturer's app, then the key will have changed already.


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

The final stage is to choose a name for the device in Home Assistant.

If you have multiple devices of the same type, you may want to change
the name to make it easier to distinguish them.

#### name

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Any unique name for the
device.  This will be used as the base for the entity names in Home
Assistant.  Although Home Assistant allows you to change the name
later, it will only change the name used in the UI, not the name of
the entities.

#### (entities)

&nbsp;&nbsp;&nbsp;&nbsp;_(boolean) (Optional)_ Additional options
may be available for deprecated entities exposed by the device.
They will be named for the platform type and an optional name for
the entity as a suffix (eg `climate`, `humidifier`, `lock_child_lock`)
Setting them to True will expose the entity in Home Assistant.

It is strongly recommended that you do not enable deprecated entities when
setting up a new device.  They are only retained for users who set up the
device before support was added for the actual entity matching the device,
or when a function was misunderstood, and will not be retained forever.

As of 0.18.0, there are no longer any deprecated entities, but they
may be reintroduced in future if better representations of existing
devices emerge again.

## Offline operation gotchas

Many Tuya devices will stop responding if unable to connect to the
Tuya servers for an extended period.  Reportedly, some devices act
better offline if DNS as well as TCP connections is blocked.

## General gotchas

Many Tuya devices do not handle multiple commands sent in quick
succession.  Some will reboot, possibly changing state in the process,
others will go offline for 30s to a few minutes if you overload them.
There is some rate limiting to try to avoid this, but it is not
sufficient for many devices, and may not work across entities where
you are sending commands to multiple entities on the same device.  The
rate limiting also combines commands, which not all devices can
handle. If you are sending commands from an automation, it is best to
add delays between commands - if your automation is for multiple
devices, it might be enough to send commands to other devices first
before coming back to send a second command to the first one, or you
may still need a delay after that.  The exact timing depends on the
device, so you may need to experiment to find the minimum delay that
gives reliable results.

Some devices can handle multiple commands in a single message, so for
entity platforms that support it (eg climate `set_temperature` can
include presets, lights pretty much everything is set through
`turn_on`) multiple settings are sent at once.  But some devices do
not like this and require all commands to set only a single dp at a
time, so you may need to experiment with your automations to see
whether a single command or multiple commands (with delays, see above)
work best with your devices.

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
temperature reaches 1 degree over the target in LOW mode, and turn on
again 3 degrees below the target.  To make these heaters act the same
in LOW power mode, you need to set the Kogan thermostat 2 degrees
higher than the GPPH thermostat.  In HIGH power mode however, they
seem to act the same as the GPPH heaters.

The Inkbird thermostat switch does not seem to work for setting
anything.  If you can figure out how to make setting temperatures and
presets work, please leave feedback in Issue #19.

## Fan gotchas

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

For the amount of consumed energy, it may be reasonable to use an additional
helper - the [Riemann integral](https://www.home-assistant.io/integrations/integration/).
Select `power` of switch as the sensor for it. The result of the integral will be
calculated in `(k/M/G/T)W*h` and will correspond to the consumed energy.

## Kogan Kettle gotchas

Although these look like simple devices, their behaviour is not
consistent so they are difficult to detect.  Sometimes they are
misdetected as a simple switch, other times they only output the
temperature sensor so are not detected at all.

## Beca thermostat gotchas

Some of these devices support switching between Celcius and Fahrenheit
on the control panel, but do not provide any information over the Tuya
local protocol about which units are selected.  Three configurations
for BHP6000 are provided, `beca_bhp6000_thermostat_c` and
`beca_bhp6000_thermostat_f`, which use Celsius and Fahrenheit
respectively, and `beca_bhp6000_thermostat_mapped` for a buggy looking
firmware which displays the temperature on the thermostat in Celsius
in increments of half a degree, but uses a slightly offset Fahrenheit
for the protocol, as detailed in issue #215.  Please select the appropriate
config for the temperature units you use.  If you change the units on the
device control panel, you will need to delete the device from Home Assistant
and set it up again.

## Saswell C16 thermostat gotchas

These support configuration as either heating or cooling controllers, but
only have one output.  The HVAC mode is provided as an indicator of which
mode they are in, but are set to readonly so that you cannot accidentally
switch the thermostat to the wrong mode from HA.


## Finding your device ID and local key

### Tuya IoT developer portal

The easiest way to find your local key is with the Tuya Developer portal.
If you have previously configured the built in Tuya cloud integration, or
localtuya, you probably already have a developer account with the Tuya app
linked.  Note that you need to use Tuya's own branded "Tuya Smart" or
"SmartLife" apps to access devices through the developer portal.  For most
devices, your device will work identically with those apps as it does with
your manufacturer's branded app, but there are a few devices where that is
not the case and you will need to decide whether you are willing to potentially
lose access to some functionality (such as mapping for some vacuum cleaners).

If you log on to your Developer Portal account, under Cloud you should
be able to get a list of your devices, which contains the "Device ID".
If you don't see them, check your server is set correctly at the top
of the page.  Make a note of the Device IDs for all your devices, then
select Cloud on the side bar again and go to the API Explorer.

Under "Devices Management", select the "Query Device Details in Bulk"
function, and enter your Device IDs, separated by commas.
In the results you should see your local_key.

The IP address you should be able to get from your router.  Using a
command line Tuya client like tuyaapi/cli or
[tinytuya](https://github.com/jasonacox/tinytuya) you may also be able
to scan your network for Tuya devices to find the IP address and also automate
the above process of connecting to the portal and getting the local key.

### Finding device ids and local keys with tinytuya

You can use this component's underlying library [tinytuya](https://github.com/jasonacox/tinytuya) to scan for devices in your network and find the required information about them. In particular, you need to use this procedure to obtain the `node_id` value required to connect to hub-dependent devices.

Before running tinytuya's wizard you need to gather your API credentials so head to [Tuya's Developer Portal](https://iot.tuya.com) -> Cloud -> Development -> Open project and make a note of:

- Access ID/Client ID
- Access Secret/Client Secret

Next, go to the "Devices" tab and note your device id (any of them will work). Also note your region (eg. "Central Europe Data Center") in the combobox at the top right of the page.

Then, open a terminal in your HA machine and run:

```sh
python -m tinytuya wizard
```

Answer the following:

- Enter API Key from tuya.com: your "Access ID/Client ID"
- Enter API Secret from tuya.com: your "Access Secret/Client Secret"
- Enter any Device ID currently registered in Tuya App (used to pull full list) or 'scan' to scan for one: your device id
- Enter Your Region: your datacenter's region
- Download DP Name mappings? (Y/n): Y
- Poll local devices? (Y/n): Y

If your device supports local connections and is in the same network as your HA instance this should find it and report its IP address.

In the `devices.json` file you will everything you need to add your device:

- "id": the device id
- "key": the local key
- "node_id": the sub-device id. You need this for hub-dependent devices
- "mapping": in the unfortunate case your device is not [yet supported](DEVICES.md), this key contains a description of all the datapoints reported by the device, type and expected values. You are more than welcome to create a new device specification following [the guidelines](custom_components/tuya_local/devices/README.md) and submitting a PR.

## Connecting to devices via hubs

If your device connects via a hub (eg. battery powered water timers) you have to provide the following info when adding a new device:

- Device id (uuid): this is the **hub's** device id
- IP address or hostname: the **hub's** IP address or hostname
- Local key: the **hub's** local key
- Sub device id: the **actual device you want to control's** `node_id`. Note this `node_id` differs from the device id, you can find it with tinytuya as described below.

## Next steps

1. This component is mostly unit-tested thanks to the upstream project, but there are a few more to complete. Feel free to use existing specs as inspiration and the Sonar Cloud analysis to see where the gaps are.
2. Once unit tests are complete, the next task is to complete the Home Assistant quality checklist before considering submission to the HA team for inclusion in standard installations.
3. Discovery seems possible with the new tinytuya library, though the steps to get a local key will most likely remain manual.  Discovery also returns a productKey, which might help make the device detection more reliable where different devices use the same dps mapping but different names for the presets for example.
>>>>>>> d624e96aceaf95655eab98168023df3aea77bb47
