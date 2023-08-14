---
name: New Device
about: Report an unsupported device.
title: Request support for [device description]
labels: new device
assignees: ''

---

<!--
This form is for reporting a new device.

When adding information, be sure to place it outside the comment blocks which
contain instructions, as these will be hidden in the submitted report.

If you are not getting any log messages when trying to add the device, then
you probably want help, which you can get by posting in
[Discussions](https://github.com/make-all/tuya-local/discussions).



Thank you for reporting a new device to add support for.  Please provide as much of the information requested below as you can.

New device requests will be processed with the following priority:

1. Pull requests
2. Issues containing logs, iot portal info with dp_ids and links that explain the usage.
3. Issues containing partial info, but probably enough to make a good guess at the likely config
4. Issues containing partial info, but some additional info needs to be requested
5. Low effort issues with virtually no useful information

Due to increasing volume of requests, it is likely that those in
category 5 will be closed without further discussion.  Those in
category 4 are likely to take some time to make it to the top of the
priority stack. 

-->

# Log Message

<!--
Please paste the message from HA log (Settings / System / Logs)
that shows the DPS returned from the device.  It is important to paste
the log message from tuya-local, rather than another source, as other
sources can strip quotes for example, which loses information about
whether certain dps are integers or strings.
-->
```
Please paste logs here
```

# Information about DPS mappings

<!--
If you have an iot.tuya.com account, please go to "Cloud" -> "API
Explorer".  Under "Device Control", select the "Query Things Data Model"
function, check the server is set correctly, and enter your device ID.
-->
```
Please paste the output here.
```

<!--
If DPS are missing from the output above, go back to the IoT Platform
"Cloud" main page and select your project.  Go to the "Devices" tab
and select "Debug Device" next to your device.  Select "Device Logs"
and open your browser's Developer Tools window on the Network tab.
For each function that has not yet been linked to a DPS, select the
function from the "Select DP ID" dropdown and press "Search".  In the
Developer Tools window, find the "list" request that was issued, and
look in the Request Payload for a "code" parameter.  This is the DP id
linked to that function, please add the remaining code and function
name here.  If the function name is in Chinese, just paste it.

If you do not have access to iot.tuya.com, please try to identify as
many DPs as possible, by experimenting with your device.  Please also
note any ranges and scale factors for input numbers, and possible
values and their meanings for any input strings (enums).
-->



# Product ID

<!--
If you have access to the IoT portal, please paste just the product_id
line from API Explorer: "Devices Management" / "Query Device Details in Bulk".
You will also find the local_key in here, please take care not to post that
publicly.  If you do, then re-pairing the device with the mobile app will
refresh the local key.

Although this information is optional and not required, it will be
used in future to identify matching devices.
-->


# Information about how the device functions

<!--
If there is a manual or other explanation available online, please
link to it (even if not in English) Otherwise if it is not obvious
what all the functions do, please give a brief description.
-->

