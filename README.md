Home Assistant Goldair WiFi Climate component
=============================================

The `goldair_climate` component integrates 
[Goldair WiFi-enabled heaters](http://www.goldair.co.nz/product-catalogue/heating/wifi-heaters) into Home Assistant, 
enabling control of setting the following parameters via the UI and the following services:

**Climate**
* **power** (on/off)
* **mode** (Comfort, Eco, Anti-freeze)
* **target temperature** (`5`-`35` in Comfort mode, `5`-`21` in Eco mode, in °C)
* **power level** (via the swing mode setting because no appropriate HA option exists: `Auto`, `1`-`5`, `Stop`)

Current temperature is also displayed.

**Sensor**
* **current temperature** (in °C)

**Light**
* **LED display** (on/off)

**Lock**
* **Child lock** (on/off)

---

### Warning
Please note, this component has currently only been tested with the Goldair GPPH (inverter) range, however theoretically 
it should also work with GEPH and GPCV devices and any other Goldair heaters based on the Tuya platform.

Work is in progress to support Goldair WiFi dehumidifiers.

---

Installation
------------
The preferred installation method is via [HACS](https://hacs.xyz/). Once you have HACS set up, simply follow the
[instructions for adding a custom repository](https://hacs.xyz/docs/navigation/settings#custom-repositories).

You can also use [Custom Updater](https://github.com/custom-components/custom_updater). Once you have Custom Updater set
up, simply go to the dev-service page
<img src="https://www.home-assistant.io/images/screenshots/developer-tool-services-icon.png" alt="The dev-service icon" width="30">
and call the `custom_updater.install` service with this service data:
```json
{ "element": "goldair_climate" }
```
Alternatively you can copy the contents of this repository's `custom_components` directory to your 
`<config>/custom_components` directory, however you will not get automatic updates this way.

Configuration
-------------
Add the following lines to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
goldair_climate:
  - name: My heater
    host: 1.2.3.4
    device_id: <your device id>
    local_key: <your local key>
    type: 'heater'
```

### Configuration variables

#### name
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* Any unique for the device; required because the Tuya API doesn't provide
                                              the one you set in the app.

#### host
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* IP or hostname of the device.

#### device_id
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* Device ID retrieved 
                                              [as per the instructions below](#finding-your-device-id-and-local-key).

#### local_key
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* Local key retrieved 
                                              [as per the instructions below](#finding-your-device-id-and-local-key).

#### type
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* The type of Goldair device. Currently `heater` is the only option; a 
                                              future update will add support for dehumidifiers and other devices, so
                                              setting the type now will prevent the component breaking when this
                                              functionality is released.

#### climate
&nbsp;&nbsp;&nbsp;&nbsp;*(boolean) (Optional)* Whether to surface this heater as a climate device.

&nbsp;&nbsp;&nbsp;&nbsp;*Default value: true* 

#### sensor
&nbsp;&nbsp;&nbsp;&nbsp;*(boolean) (Optional)* Whether to surface this heater's thermometer as a temperature sensor.

&nbsp;&nbsp;&nbsp;&nbsp;*Default value: false* 

#### display_light
&nbsp;&nbsp;&nbsp;&nbsp;*(boolean) (Optional)* Whether to surface this heater's LED display control as a light.

&nbsp;&nbsp;&nbsp;&nbsp;*Default value: false* 

#### child_lock
&nbsp;&nbsp;&nbsp;&nbsp;*(boolean) (Optional)* Whether to surface this heater's child lock as a lock device.

&nbsp;&nbsp;&nbsp;&nbsp;*Default value: false* 

Gotchas
-------
These heaters have individual target temperatures for their Comfort and Eco modes, whereas Home Assistant only supports
a single target temperature. Therefore, when you're in Comfort mode you will set the Comfort temperature (`5`-`35`), and
when you're in Eco mode you will set the Eco temperature (`5`-`21`), just like you were using the heater's own control 
panel. Bear this in mind when writing automations that change the operation mode and set a temperature at the same time: 
you must change the operation mode *before* setting the new target temperature, otherwise you will set the current 
thermostat rather than the new one. 

When switching to Anti-freeze mode, the heater will set the current power level to `1` as if you had manually chosen it.
When you switch back to other modes, you will no longer be in `Auto` and will have to set it again if this is what you
wanted. This could be worked around in code however it would require storing state that may be cleared if HA is
restarted and due to this unreliability it's probably best that you just factor it into your automations.

When child lock is enabled, the heater's display will flash with the child lock symbol (`[]`) whenever you change
something in HA. This can be confusing because it's the same behaviour as when you try to change something via the
heater's own control panel and the change is rejected due to being locked, however rest assured that the changes *are* 
taking effect.

Finding your device ID and local key 
------------------------------------
You can find these keys the same way as you would for any Tuya local component. You'll need the Tuya Smart app rather 
than the Goldair app (the Goldair app is just a re-branded clone of Tuya Smart).

* [Instructions for iOS](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)
* [Instructions for Android](https://github.com/codetheweb/tuyapi/blob/cdb4289/docs/SETUP_DEPRECATED.md#capture-https-traffic)

You're looking for `uuid` (this is the device ID) and the `localKey` values.

Next steps
----------
This component needs specs! Once they're written I'm considering submitting it to the HA team for inclusion in standard 
installations. Please report any issues and feel free to raise pull requests.

I also have a working integration for Goldair WiFi dehumidifiers; it needs to be re-worked to prevent duplicate code
before releasing it to the wild.

Acknowledgements
----------------
None of this would have been possible without some foundational discovery work to get me started:

* [TarxBoy](https://github.com/TarxBoy)'s [investigation using codetheweb/tuyapi](https://github.com/codetheweb/tuyapi/issues/31) to figure out the correlation of the cryptic DPS states 
* [sean6541](https://github.com/sean6541)'s [tuya-homeassistant](https://github.com/sean6541/tuya-homeassistant) library giving an example of integrating Tuya devices with Home Assistant
* [clach04](https://github.com/clach04)'s [python-tuya](https://github.com/clach04/python-tuya) library
