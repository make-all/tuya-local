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

Requests for new devices without logs from this integration containing
dps information are not actionable, and will be closed without further action.


Thank you for reporting a new device to add support for.  Please provide as much of the information requested below as you can.

New device requests will be processed with the following priority:

1. Pull requests
2. Issues containing logs, iot portal info with dp_ids and links that explain the usage.
3. Issues containing logs and information about the main dps required to make the device function, including range of any settable integer dps, and all possible values for any settable string dps.

Due to increasing volume of requests, those not meeting the above
requirements will be closed without further discussion.

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

Alternatively, tools that do local discovery, such as tinytuya, may be able
to show the product id without needing access to the developer portal.

Although this information is optional and not required, it will be
used in future to identify matching devices.
-->


# Information about how the device functions

<!--
If there is a manual or other explanation available online, please
link to it (even if not in English) Otherwise if it is not obvious
what all the functions do, please give a brief description.
-->
