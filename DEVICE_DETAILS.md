This information has been split out from the main README.md, as the cloud
assisted config flow has been added as more user friendly way to get device
details from the cloud, making the below steps optional, and only of interest
if you manually configure the devices.

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
