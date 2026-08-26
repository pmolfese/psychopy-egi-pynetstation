Troubleshooting
===============

The EGI Components do not appear
--------------------------------

Install the plugin into PsychoPy's own Python environment and restart
PsychoPy. Builder discovers the Components from package entry points only at
startup. Look under **I/O > EEG**.

Nothing appears in Device Manager
---------------------------------

This is expected. NetStation amplifiers cannot be auto-discovered, and
**Device label** is an internal text key rather than a Device Manager
selection. Enter all network settings in EGI Connect.

“No NetStation device found” at startup
---------------------------------------

Add EGI Connect before the failing Component and make their **Device label**
values identical. The default is ``netstation``. Check capitalization and
whitespace if custom labels are used.

Connection refused or timed out
-------------------------------

Confirm that ECI is enabled, the NetStation host address and port are correct,
both computers can reach each other, and host firewalls permit the connection.
The default ``10.10.10.42`` is an example lab address, not a universal value.

Clock synchronization fails
---------------------------

Confirm that **Amplifier NTP IP address** points to an NTP server reachable
from the PsychoPy computer. Leaving the field blank reuses the NetStation host
address, which is only correct when that host provides the required NTP
service.

No event markers arrive
-----------------------

Start recording before sending markers. Ensure **Event type** is exactly four
characters and inspect the PsychoPy log at experiment end for both
asynchronous worker failures and rejected ECI responses. Stop recording or
disconnect cleanly so queued events can flush. For detailed diagnostics, set a
writable **ECI error log file** and optionally enable **Strict ECI responses**
in EGI Connect. Coder experiments can inspect ``sessionSummary()``,
``eventErrors()``, and ``eciErrors()`` directly.

“This connection has already recorded”
--------------------------------------

One connection supports one recording epoch because starting again would
rebase the event clock. Stop recording, disconnect, reconnect, and then start
the next recording. Do not place a second EGI Start Recording Component before
an intervening EGI Disconnect and EGI Connect pair.

Markers do not align with a visual stimulus
--------------------------------------------

Enable **Sync to screen refresh** on EGI Send Event and give it the same start
condition as the visual stimulus. Do not confuse this with EGI Connect's
inherited **Sync timing with screen refresh** option.

A one-frame timing step appears
-------------------------------

Keep EGI Connect's display measurement and schedule warning enabled, then
inspect the startup log. A clock-timed duration that is not a whole number of
measured frame periods can produce a display phase sweep even when event
timestamps are correct. See :doc:`timing` before changing durations to frames.

Debug output is overwhelming
----------------------------

Disable **Debug ECI traffic** after diagnosing the issue. It prints every
protocol command and response byte and is not intended for routine data
collection.
