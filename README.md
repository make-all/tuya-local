# Home Assistant Tuya Local component

Please report any [issues](https://github.com/make-all/tuya-local/issues) and feel free to raise [pull requests](https://github.com/make-all/tuya-local/pulls).
[Many others](https://github.com/make-all/tuya-local/blob/main/ACKNOWLEDGEMENTS.md) have contributed their help already.

[![BuyMeCoffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jasonrumney)

This is a Home Assistant integration to support devices running Tuya
firmware without going via the Tuya cloud.  Devices are supported
over WiFi, limited support for devices connected via hubs is available.

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

Sub devices should be added using the `device_id`, `address` and `local_key`
of the hub they are attached to, and the `node_id` of the sub-device. If there
is no `node_id` listed, try using the `uuid` instead.

Tuya Zigbee devices are usually standard zigbee devices, so as an
alternative to this integration with a Tuya hub, you can use a
supported Zigbee USB stick or Wifi hub with
[ZHA](https://www.home-assistant.io/integrations/zha/#compatible-hardware)
or [Zigbee2MQTT](https://www.zigbee2mqtt.io/guide/adapters/).

Some Tuya Bluetooth devices can be supported directly by the
[tuya_ble](https://github.com/PlusPlus-ua/ha_tuya_ble/) integration.

Tuya IR hubs that expose general IR remotes as sub devices usually
expose them as one way devices (send only).  Due to the way this
integration does device detection based on the dps returned by the
device, it is not currently able to detect such devices at all.  Some
specialised IR hubs for air conditioner remote controls do work, as
they try to emulate a fully smart air conditioner using internal memory
of what settings are currently set, and internal temperature and humidity
sensors.

Some Tuya hubs now support Matter over WiFi, and this can be used as an
alternative to this integration for connecting the hub and sub-devices
to Home Assistant. Other limitations will apply to this, so you might want
to try both, and only use this integration for devices that are not working
properly over Matter.

A list of currently supported devices can be found in the [DEVICES.md](https://github.com/make-all/tuya-local/blob/main/DEVICES.md) file.

Documentation on building a device configuration file is in [/custom_components/tuya_local/devices/README.md](https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/README.md)

If your device is not listed, you can find the information required to add a configuration for it in the following locations:

1. When attempting to add the device, if it is not supported, you will either get a message saying the device cannot be recognised at all, or you will be offered a list of devices that are partial matches. You can cancel the process at this point, and look in the Home Assistant log - there should be a message there containing the current data points (dps) returned by the device.
2. If you have signed up for [iot.tuya.com](https://iot.tuya.com/), you should have access to the API Explorer under "Cloud". Under "Device Control" there is a function called "Query Things Data Model", which returns the dp_id in addition to range information that is needed for integer and enum data types.

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

### Choose your configuration path

There are two options for configuring a device:
- You can login to Tuya cloud with the Smart Life app and retrieve a list of devices and the necessary local connection data.
- You can provide all the necessary information manually [as per the instructions below](#finding-your-device-id-and-local-key).

The first choice essentially automates all the manual steps of the second and without needing to create a Tuya IOT developer account. This is especially important now that Tuya has started time limiting access to a key data access capability in the IOT developer portal to only a month with the ability to refresh the trial of that only every 6 months.

The cloud assisted choice will guide you through authenticating, choosing a device to add from the list of devices associated with your Smart Life account, locate the device on your local subnet and then drop you into [Stage One](#stage-one) with fully populated data necessary to move forward to [Stage Two](#stage-two).

The Smart Life authentication token expires after a small number of hours and so is not saved by the integration. But, as long as you don't restart Home Assistant, this allows you to add multiple devices one after another only needing to authenticate once for the first one.

### Stage One

The first stage of configuration is to provide the information needed to connect to the device.

When using the cloud assisted config, the device id and local key will be pre-filled from the cloud, and the IP address will also be filled if local discovery is not blocked by other integrations or a complex network setup. Otherwise, see [DEVICE_DETAILS.md](DEVICE_DETAILS.md) for instructions on how to find the info.

#### host

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ IP or hostname of the device.

#### device_id

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Device ID retrieved

#### local_key

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Local key retrieved

Note that each time you pair the device, the local key changes, so if you obtained the local key using the instructions below, then re-paired with your manufacturer's app, then the key will have changed already.

#### protocol_version

&nbsp;&nbsp;&nbsp;&nbsp;_(string or float) (Required)_ Valid options are "auto", 3.1, 3.2, 3.3, 3.4, 3.5, 3.22.  If you aren't sure, choose "auto", but some 3.2, 3.22 and maybe 3.4 devices may be misdetected as 3.3 (or vice-versa), so if your device does not seem to respond to commands reliably, try selecting between those protocol versions. Protocol 3.22 is a special case, that enables tinytuya's "device22" detection with protocol 3.3. Previously we let tinytuya auto-detect this, but it was found to sometimes misdetect genuine 3.3 devices as device22 which stops them receiving updates, so an explicit version was added to enable the device22 detection.

At the end of this step, an attempt is made to connect to the device and see if
it returns any data. For tuya protocol version 3.1 devices, the local key is
only used for sending commands to the device, so if your local key is
incorrect the setup will appear to work, and you will not see any problems
until you try to control your device.  For more recent Tuya protocol versions,
the local key is used to decrypt received data as well, so an incorrect key
will be detected at this step and cause an immediate failure.


### Stage Two

The second stage of configuration is to select which device you are connecting.
The list of devices offered will be limited to devices which appear to be
at least a partial match to the data returned by the device.

#### type

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Optional)_ The type of Tuya device.
Select from the available options.

The list presented is filtered to exclude devices that definitely do not match among the 1000+ supported devices. If a device config you expected is not shown, you may have a different firmware version, so the best way to report this is as a new device.

If you pick the wrong type, you will need to delete the device and set
it up again. This is because different types of devices create different
entities, so changing the device type without deleting everything is
not advisable.

### Stage Three

The final stage is to choose a name for the device in Home Assistant.

If you have multiple devices of the same type, you may want to change
the name to make it easier to distinguish them.

#### name

&nbsp;&nbsp;&nbsp;&nbsp;_(string) (Required)_ Any unique name for the
device.  This will be used as the base for the entity names in Home
Assistant.

## Offline operation issues

Many Tuya devices will stop responding if unable to connect to the
Tuya servers for an extended period.  Reportedly, some devices act
better offline if DNS as well as TCP connections is blocked.

## General issues

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

When adding devices, some devices that are detected as protocol version
3.3 at first require version 3.2 to work correctly. Either they cannot be
detected, or work as read-only if the pprotocol is set to 3.3.

## Connecting to devices via hubs

If your device connects via a hub (eg. battery powered water timers) you have to provide the following info when adding a new device:

- Device id (uuid): this is the **hub's** device id
- IP address or hostname: the **hub's** IP address or hostname
- Local key: the **hub's** local key
- Sub device id: the **actual device you want to control's** `node_id`. Note this `node_id` differs from the device id, you can find it with tinytuya as described below.

## Contributing

Beyond contributing device configs, here are some areas that could benefit from more hands:

1. Unit tests. This integration is mostly unit-tested thanks to the upstream project, but there are a few more to complete. Feel free to use existing specs as inspiration and the Sonar Cloud analysis to see where the gaps are.
2. Once unit tests are complete, the next task is to properly evaluate against the Home Assistant quality scale. 
3. Discovery. Local discovery is currently limited to finding the IP address in the cloud assisted config. Performing discovery in background would allow notifications to be raised when new devices are noticed on the network, and would provide a productKey for the manual config method to use when matching device configs.
