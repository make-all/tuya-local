Home Assistant Goldair WiFi Heater platform
===========================================

The `goldair_heater` platform integrates [Goldair WiFi-enabled heaters](http://www.goldair.co.nz/product-catalogue/heating/wifi-heaters) into Home Assistant, enabling control of setting the following parameters via the UI and climate service:

* **power** (on/off)
* **mode** (Comfort, Eco, Anti-freeze)
* **target temperature** (`5`-`35` representing °C)

and additionally the following parameters via `configuration.yaml`:

* **power_level** (auto, `1`-`5`)
* **display** (on/off)
* **child_lock** (on/off)

Current temperature is displayed.

---

### Warning
Please note, this platform has currently only been tested with the Goldair GPPH (inverter) range, however theoretically it should also work with GEPH and GPCV devices and any other Goldair heaters based on the Tuya platform.

---

To enable the platform, copy `goldair_heater.py` to the `<config_dir>/custom_components/climate` directory, then add the following lines to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
climate:
  - platform: goldair_heater
    name: My heater
    host: 1.2.3.4
    device_id: <your device id>
    local_key: <your local key>
```

CONFIGURATION VARIABLES
-----------------------

### name
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* Any unique for the device; required because the Tuya API doesn't provide the one you set in the app.

### host
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* IP or hostname of the device.

### device_id
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* Device ID retrieved from the Goldair app logs (see below).

### local_key
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Required)* Local key retrieved from the Goldair app logs (see below).

### power_level
&nbsp;&nbsp;&nbsp;&nbsp;*(string) (Optional)* Set the power level you want to use. `auto` is recommended, though the heaters also support `stop` (no heat at all) or `1` through `5`. Bear in mind that this is a once-off setting because the HA climate interface doesn't yet have a control or service that suits this property.

### display_on
&nbsp;&nbsp;&nbsp;&nbsp;*(boolean) (Optional)* Whether to enable the LED display or not. 

### child_lock
&nbsp;&nbsp;&nbsp;&nbsp;*(boolean) (Optional)* Whether to enable the child lock or not. 

FINDING YOUR DEVICE ID AND LOCAL KEY
------------------------------------

If you have an Android device that supports Mass Storage mode, you can easily find these properties using the below instructions. If you don't, there are some alternate methods at [codetheweb/tuyapi](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md) (you're looking for the `uuid` and `localKey` values).

1. Download the [Goldair app from the Play Store](https://play.google.com/store/apps/details?id=com.goldair.smart).
2. Follow the instructions in the app to set up the heater. Don't agonise over the name because you'll be giving it a new one in HA, but do remember it because you'll use this name to find the keys later.
3. Once this is done and you've verified that you can control the heater from your phone, close the app and plug your phone into a computer in Mass Storage mode (choose the option to browse files). 
    * ℹ Alternatively you can use an Android file browser, but bear in mind you will need to search through a large log file
4. Browse your phone's filesystem to find `/Android/data/com.goldair.smart/cache/1.abj` and open it in a text editor that can handle large files.
5. Search for your device in this file by the name you gave it earlier. You're looking for a very long line that contains not only the device name, but also `uuid` and `localKey` properties. 
    * ℹ If you've been using the app a while and have added this device more than once, you need to find the last occurrence of this kind of line for your device in the log file
6. Copy the value of `uuid` (eg: 1234567890abcdef1234) to `device_id`, and the value of `localKey` (eg: 1234567890abcdef) to `local_key` in your `configuration.yaml` file.

Repeat for as many heaters as you have to set up.

NEXT STEPS
----------
This platform needs specs! Once they're written I'm considering submitting it to the HA team for inclusion in standard installations. Please report any issues and feel free to raise pull requests.

It would be great to support changing of the power level and setting of the timer via the HA interface and automation. Any ideas on how to do this would be much appreciated; I suspect it may end up being a combination of multiple platform types.

This was my first Python project, so feel free to correct any conventions or idioms I got wrong.

ACKNOWLEDGEMENTS
----------------
All I did was write some code. None of this would have been possible without:

* [TarxBoy](https://github.com/TarxBoy)'s [investigation using codetheweb/tuyapi](https://github.com/codetheweb/tuyapi/issues/31) to figure out the correlation of the cryptic DPS states 
* [sean6541](https://github.com/sean6541)'s [tuya-homeassistant](https://github.com/sean6541/tuya-homeassistant) library giving an example of integrating Tuya devices with Home Assistant
* [clach04](https://github.com/clach04)'s [python-tuya](https://github.com/clach04/python-tuya) library
