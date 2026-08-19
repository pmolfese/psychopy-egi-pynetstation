# PsychoPy EGI NetStation

`psychopy-egi-pynetstation` adds EGI/Magstim NetStation recording control and
event markers to [PsychoPy](https://www.psychopy.org/) Builder and Python
experiments. It uses the NetStation ECI network protocol through the
[egi-pynetstation](https://github.com/nimh-sfim/egi-pynetstation) package.

The plugin provides five Builder Components for connecting, starting and
stopping recording, sending events, and disconnecting. Network settings are
entered directly in **EGI Connect**. No physical device selection or prior
PsychoPy Device Manager configuration is required.

> **Validation status:** version 0.1.0 is the initial public-release candidate. Automated
> tests cover the wrapper API, generated Builder code, event defaults, and
> display-timing helpers. End-to-end validation against a physical or simulated
> NetStation amplifier is still in progress; validate the complete workflow in
> your lab before collecting production data.

## Requirements

- Python 3.10 or newer
- PsychoPy 2026.1 or newer
- A network-reachable NetStation host with ECI enabled
- The NetStation host IP, ECI port (normally `55513`), and amplifier NTP IP

`egi-pynetstation>=2.0.0` is installed automatically with this plugin.

## Installation

After the first PyPI release, install the package from PsychoPy's
Plugin/Packages Manager by searching for `psychopy-egi-pynetstation`, or run:

```bash
python -m pip install psychopy-egi-pynetstation
```

Restart PsychoPy after installation so Builder discovers the plugin. Until the
first PyPI release is available, install the current source directly from
GitHub:

```bash
python -m pip install git+https://github.com/pmolfese/psychopy-egi-pynetstation.git
```

For development from a local checkout:

```bash
python -m pip install -e ".[tests]"
```

You will not necessarily see an explicit `import egi_pynetstation` in a
Builder-generated experiment. PsychoPy discovers this plugin through its
installed entry points, and the plugin's hardware wrapper imports the underlying
network library internally.

## Builder quick start

Add the Components to the Flow in this order, keeping the default Device label
`netstation` on all of them:

1. Add **EGI Connect** near the start of the experiment. Enter the NetStation
   host IP, ECI port, and amplifier NTP IP on its **Device** tab.
2. Add **EGI Start Recording** after the connection is established.
3. Add **EGI Send Event** wherever a marker should be emitted. Event type must
   be four characters, such as `stim` or `resp`. Event duration defaults to
   `0.1` seconds.
4. Add **EGI Stop Recording** near the end of the experiment.
5. Add **EGI Disconnect** after recording has stopped.

These Components are momentary commands: their Component stop time/duration is
not used. For **EGI Send Event**, the separate **Event duration (s)** field is
the duration recorded in NetStation and defaults to `0.1`.

The shared Device label is only an internal name used by the generated script
to retrieve one network connection. It is plain text, not a device to select
from Device Manager. NetStation amplifiers are not auto-discovered, so an empty
Device Manager list is expected.

## Python usage

```python
from psychopy.hardware import DeviceManager

ns = DeviceManager.addDevice(
    deviceClass="psychopy_egi_pynetstation.hardware.netstation.EGINetStation",
    deviceName="netstation",
    ip="10.10.10.42",     # NetStation host computer
    ntpIP="10.10.10.51",  # amplifier NTP server
    port=55513,            # ECI port
)

ns.connect()
ns.beginRecording()

# Mark stimulus onset on the flip that actually shows it.
win.callOnFlip(
    ns.sendEvent,
    eventType="stim",
    label="face",
    duration=0.1,
)
win.flip()

ns.endRecording()
ns.disconnect()
```

Event sending is asynchronous. Check `ns.eventErrors()` before accepting a run;
the Builder integration performs this check automatically at experiment end.

## Builder Components

Five Builder Components are also included, under **I/O > EEG** in the Components panel -
each is a one-shot "command" that fires once, when the Component starts (their stop
time/duration is not used):

1. **EGI Connect** - creates the NetStation network client, registers it internally,
   then opens the TCP/IP connection. Set the **NetStation IP address** (default
   `10.10.10.42`), **port** (default `55513`), **Amplifier NTP IP address**
   (default `10.10.10.51`), **endianness** and **drift
   correction** mode here. Background drift sampling is the default and needs no extra
   Component. Add exactly one of these per amplifier, before any other NetStation
   Component.
2. **EGI Start Recording** - starts EEG recording, and performs the ECI NTP sync
   which establishes the event timestamp epoch.
3. **EGI Stop Recording** - stops EEG recording (flushing queued events first).
4. **EGI Disconnect** - closes the connection (flushing queued events first).
5. **EGI Send Event** - sends a single event marker (4-character **Event
   type**, plus optional label/description/extra data). **Event duration** defaults
   to `0.1` seconds. With **Sync to screen refresh** on (the default) the marker is
   sent from `win.callOnFlip()`, so it is timestamped to the flip which actually
   showed the stimulus.

All five share a **Device label** text parameter (default `"netstation"`) - Start/Stop
Recording, Disconnect and Send Event all look up the network client that Connect
registered under the same label, so keep the label consistent across all NetStation
Components in an experiment. This is an internal name, not a device to select in
PsychoPy's Device Manager; no Device Manager setup is required. If no matching
Connect Component is found, the generated script raises a clear `ValueError` at
experiment startup rather than failing obscurely later. Drop these into your
Routines/Flow in the order matching the numbering above (Connect near the start of
the experiment, Disconnect near the end).

### Drift correction

Connect's **Drift correction** setting has two modes:

| Mode | You must | Forgetting to wire it up |
|---|---|---|
| **Background thread** | nothing | cannot happen |
| **Off** | nothing | n/a |

Background sampling is the upstream default because it keeps drift correction alive
without asking the experiment to provide inter-trial sampling windows. Advanced
cooperative/manual drift methods still exist on the Python wrapper for custom code, but
they are no longer exposed as Builder buttons.

### ECI endianness

The **Endianness** setting is the ECI protocol byte order for the computer running
PsychoPy, not the amplifier.

| ECI option | Protocol meaning | Real-world use |
|---|---|---|
| `NTEL` | Little-endian | Modern Intel Macs, Apple Silicon Macs, Windows x86/x64, most ARM64 Linux |
| `MAC-` | Big-endian | Legacy PowerPC-era Macs |
| `UNIX` | Big-endian | Legacy big-endian Unix systems; misleading for most modern Unix/Linux |

### Display timing and the frame beat

A display refreshes on a fixed heartbeat; your experiment asks for stimuli on
its own schedule. When an inter-stimulus interval is not a whole number of
refresh periods, the request creeps through the refresh cycle a little each
trial - and because a display can only present at a frame boundary, that creep
surfaces as a sudden **one-frame (16.7 ms) step**, with nothing in the software
looking any different.

This is a display problem, not a marker problem. Event timestamps were never
wrong, and `egi-pynetstation` never sees a frame. The plugin's job here is to
**measure, record and advise** - it deliberately does not reschedule anything,
because silently changing your timing behaviour would be worse than the
original problem.

Connect's **Display** tab has two settings:

- **Measure display refresh at startup** *(default on)* - measures the real
  refresh once via `getActualFrameRate()`, falling back to the monitor
  configuration and then to 60 Hz with a warning. Takes 1-2 s and drops
  frames, so it runs at setup only, never during trials. The result is logged
  and written to the ECI error log as a `display_timing` record.

  This matters because **the effect is invisible at exactly 60.000 Hz**, where
  every common interval is a whole number of frames. A display at 60.00043 Hz
  - 7 parts per million fast - puts a 3 s interval at 180.0013 frames, and the
  onset phase sweeps a whole frame every ~39 minutes. Without the measured
  rate, a one-frame step afterwards is indistinguishable from a marker bug.

- **Warn about vulnerable schedules** *(default on)* - compares your Routine
  durations against the measured refresh and warns once at startup:

  ```
  WARNING: NetStation display timing: 3 s is 0.00129 frame off a whole number
  at 60.0004 Hz. Under clock timing the stimulus onset phase sweeps a full
  frame about every 39 min, which can produce a one-frame (16.7 ms) step in
  stimulus presentation. Consider specifying durations in frames.
  ```

  Durations are harvested at build time and **weighted by how often each
  Routine runs**, so the beat reported is the one most of your trials actually
  experience. Reporting the worst-rounding interval instead would badly
  overstate the risk whenever one interval dominates a design. The worst case
  is still reported, separately and labelled as such.

  Only Routines whose length is fully fixed are checked. A Routine ended by a
  keypress has no fixed interval for a beat to build against, so it is skipped
  - correctly, not as a limitation.

**The fix, when you need it, is Builder's own:** set durations in **frames**
rather than seconds, so there is only one rhythm. Two costs worth knowing: the
interval becomes 180 x 16.6665 ms = 2.99997 s rather than exactly 3.000 s, and
dropped frames accumulate permanently instead of self-correcting the way
clock-based waiting does. That trade is usually worth it when
stimulus-to-stimulus consistency matters more than absolute schedule.

Frame counting removes the phase sweep for certain. Whether it removes the
one-frame step is still being tested: with a compositor in the path, `flip()`
returning means the buffer was *accepted*, not *displayed*, so the mechanism
linking the two has not been fully isolated. Treat this as removing a known
systematic risk, not as a guarantee about stimulus timing. If your logs show
onset lateness flat but a step persisting, the cause is downstream of the flip
and the plugin cannot help.

The formulas are available directly for your own analysis:

```python
from psychopy_egi_pynetstation.timing import frameSlip, beatSeconds, framesFor

framePeriod = 1.0 / 60.00043
frameSlip(3.0, framePeriod)      # 0.00129 frames off a whole number
beatSeconds(3.0, framePeriod)    # 2328 s -> a full frame every ~39 min
framesFor(3.0, framePeriod)      # 180 frames, for frame-based scheduling
```

### Asynchronous events

Event sending is unconditionally asynchronous upstream, which is what makes
flip-synced markers safe. A failed send therefore cannot raise into experiment code, so
the Connect Component writes an end-of-experiment check that reports any failures via
`logging.error` - bad runs don't pass silently.

## Troubleshooting

- **Nothing appears in Device Manager:** expected. Configure the IP and port in
  EGI Connect instead.
- **The EGI Components do not appear:** confirm the plugin is installed into
  PsychoPy's Python environment, then restart PsychoPy.
- **Connection refused or times out:** confirm ECI is enabled, the host IP and
  port are correct, both computers can reach each other, and local firewall
  rules allow the connection.
- **No event markers arrive:** start recording before sending events and inspect
  the experiment log for asynchronous event errors.
- **Clock synchronization fails:** confirm the amplifier NTP IP is reachable
  from the experiment computer.

## Development

Run the test suite and verify the distributable files with:

```bash
python -m pytest
python -m build
python -m twine check dist/*
```

The full Builder tests require PsychoPy. Tests that do not require PsychoPy or
an amplifier still run in a lightweight Python environment. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the contribution and hardware-validation
workflow.

## License

This is a United States Government work and is in the public domain in the
United States. The MIT License applies where US public-domain status does not.
See [LICENSE](LICENSE) for the full notice.

### Attribution

Attribution can't be legally required for a US Government work, and the license
imposes no such condition - but it is requested. If this plugin supports
published research, please cite it and acknowledge **Peter J. Molfese** and the
**NIH Center for Multimodal Neuroimaging**
([CMN](https://cmn.nimh.nih.gov)), along with the underlying
[egi-pynetstation](https://github.com/nimh-sfim/egi-pynetstation) package.
