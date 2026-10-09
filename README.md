# PsychoPy EGI NetStation

[![PyPI](https://img.shields.io/pypi/v/psychopy-egi-pynetstation.svg)](https://pypi.org/project/psychopy-egi-pynetstation/)
[![Documentation Status](https://readthedocs.org/projects/psychopy-egi-pynetstation/badge/?version=latest)](https://psychopy-egi-pynetstation.readthedocs.io/en/latest/)

`psychopy-egi-pynetstation` adds EGI/Magstim NetStation recording control and
event markers to [PsychoPy](https://www.psychopy.org/) Builder and Python
experiments. It uses the NetStation ECI network protocol through the
[egi-pynetstation](https://github.com/nimh-sfim/egi-pynetstation) package.

> [!NOTE]
> **Independent community project**
>
> This plugin is not associated with, affiliated with, endorsed by, or
> sponsored by EGI or Magstim EGI. It is an independent, community-maintained
> solution for using NetStation with PsychoPy.

Use the plugin in any of three ways: with three PsychoPy Studio or desktop
Builder Components backed by Device Manager, by directly constructing the
Python hardware wrapper, or through Device Manager from Coder.

> **Validation status:** version 0.1.0 has been exercised end to end with a
> NetStation system. Automated tests cover the wrapper API, generated Builder
> code, event defaults, and display-timing helpers. Validate the complete
> workflow on your own lab hardware before collecting production data.

## Requirements

- Python 3.10 or newer
- PsychoPy 2026.1 or newer
- A network-reachable NetStation host with ECI enabled
- The NetStation host IP, ECI port (normally `55513`), and amplifier NTP IP

`egi-pynetstation>=2.1.0` is installed automatically with this plugin.

## Installation

Install the package from PsychoPy's Plugin/Packages Manager by searching for
`psychopy-egi-pynetstation`, or run:

```bash
python -m pip install psychopy-egi-pynetstation
```

Restart PsychoPy after installation so Studio discovers the plugin.

For development from a local checkout:

```bash
python -m pip install -e ".[tests]"
```

You will not necessarily see an explicit `import egi_pynetstation` in a
Builder-generated experiment. PsychoPy discovers this plugin through its
installed entry points, and the plugin's hardware wrapper imports the underlying
network library internally.

## Builder and Studio quick start

Both PsychoPy Studio and the classic desktop Builder in supported PsychoPy
2026.1+ releases provide Device Manager. Neither interface needs a Connect or
Disconnect Component. PsychoPy versions before 2026.1 are not supported by
this plugin.

Configure the device once, then add the Components to the Flow:

1. Open Studio's **Device Manager**, choose **Add Device > EGI NetStation**,
   select the manual-configuration profile, and give it the label `netstation`.
   Enter the NetStation host IP, ECI port, amplifier NTP IP, and any drift or
   diagnostic options. The generated experiment connects during device setup.
2. Add **EGI Start Recording** where recording should begin and select the
   `netstation` device.
3. Add **EGI Send Event** wherever a marker should be emitted. Select the same
   device. Event type must be four characters, such as `stim` or `resp`. Event
   duration defaults to
   `0.1` seconds.
4. Add **EGI Stop Recording** near the end of the experiment.

These Components are momentary commands: their Component stop time/duration is
not used. For **EGI Send Event**, the separate **Event duration (s)** field is
the duration recorded in NetStation and defaults to `0.1`.

NetStation amplifiers cannot be auto-discovered, so Device Manager presents a
manual configuration profile rather than claiming that hardware was found.
PsychoPy closes registered devices at experiment shutdown; the wrapper's
idempotent `close()` and destructor safely stop an active recording, flush
queued events, and disconnect.

Device Manager profiles are saved in PsychoPy's per-user `devices.json`, not
inside the `.psyexp` file. The experiment stores only the selected device
label. When moving the experiment to another computer or user account, install
the plugin and recreate/import an EGI NetStation profile with the same label
before generating the experiment script. The generated Python script contains
the resolved device setup code.

## PsychoPy Coder / Python quick start

Builder is optional. In PsychoPy Coder—or any Python experiment using a
PsychoPy window—the smallest setup is to import and construct the hardware
wrapper directly. Explicit plugin activation is not required:

```python
from psychopy import visual
from psychopy_egi_pynetstation import EGINetStation

win = visual.Window()
ns = EGINetStation(
    ip="10.10.10.42",     # NetStation host computer
    ntpIP="10.10.10.51",  # amplifier NTP server
    port=55513,            # ECI port
)
try:
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
finally:
    # Stops an active recording, flushes queued events, and disconnects.
    ns.close()
    win.close()
```

### Coder with PsychoPy DeviceManager

If the Coder experiment already uses PsychoPy's device registry, replace the
direct `EGINetStation(...)` construction above with:

```python
from psychopy.hardware import DeviceManager

ns = DeviceManager.addDevice(
    deviceClass="psychopy_egi_pynetstation.hardware.netstation.EGINetStation",
    deviceName="netstation",
    ip="10.10.10.42",
    ntpIP="10.10.10.51",
    port=55513,
)
```

This returns the same `EGINetStation` interface, so the remaining
`connect()`/`beginRecording()`/`sendEvent()`/`close()` code is unchanged. The
device can later be retrieved with
`DeviceManager.getDevice("netstation")`.

### Why `EGINetStation` instead of `NetStation`?

The underlying [`egi-pynetstation`](https://github.com/nimh-sfim/egi-pynetstation)
package calls its low-level network client `NetStation`:

```python
from egi_pynetstation import NetStation
```

This plugin calls its PsychoPy-compatible wrapper `EGINetStation` to distinguish
the two classes when both packages appear in the same program. It is still the
same EGI/Magstim NetStation hardware; the `EGI` prefix identifies the wrapper,
which adds PsychoPy `BaseDevice`, Builder, logging, drift, and cleanup behavior.

Event sending is asynchronous. `close()` flushes queued events and reports
worker failures, rejected ECI responses, and drift-health problems through
PsychoPy's logger. Use `ns.sessionSummary()` for the combined result;
`ns.eventErrors()` and `ns.eciErrors()` provide the two failure categories
separately. The Builder integration performs the same safe cleanup
automatically at experiment end.

For a diagnostic run, or before a block whose first markers should wait for an
engaged drift model, call the upstream-style readiness wait after recording
starts and before timing-critical events:

```python
ns.connect()
ns.beginRecording()
ns.waitForDrift(timeout=300.0, poll=1.0)
```

`waitForDrift()` wraps `egi-pynetstation`'s
`wait_for_drift(timeout=300.0, poll=1.0, on_wait=None, **ready_options)`, and
the plugin also exposes `wait_for_drift()` for code copied from upstream
examples. Because it intentionally blocks, use it during setup or a planned
pre-run pause, never inside `win.callOnFlip()` or near a visual flip.

### Save the drift model and diagnostics

The standard drift-model output is a JSON-lines diagnostics file. In Builder
or Studio, set **Device Manager > EGI NetStation > Data > ECI error log file**
to a writable `.jsonl` path. Despite the option's historical name, the file is
not limited to errors: it automatically records the session's effective drift
settings, clock information, model engagement and promotion, periodic
`drift_model_status` updates, and any ECI or drift failures. No per-trial code
is required.

In Python, supply the same path when the device is constructed:

```python
ns = EGINetStation(..., errorLog=diagnostics_path)
```

To add a complete snapshot of the current model at a meaningful point, such
as the end of a block, append it to that configured file with one line:

```python
ns.logRecord({"record": "drift_model_snapshot", **ns.driftEstimate()})
```

Take explicit snapshots between trials or during cleanup, not in
`win.callOnFlip()` or another timing-critical callback. `driftEstimate()`
returns the current model as a dictionary; `driftSettings()` returns the
settings actually in effect.

## Builder and Studio Components

Three Components appear under **I/O > EEG** in Studio and supported desktop
Builder releases. Each uses the EGI NetStation device selected from Device
Manager and fires once when the Component starts (its normal stop time/duration
is not used):

1. **EGI Start Recording** - starts EEG recording, and performs the ECI NTP sync
   which establishes the event timestamp epoch. It can optionally wait until
   drift correction is ready before the experiment continues. One connection
   supports one recording epoch.
2. **EGI Stop Recording** - stops EEG recording (flushing queued events first).
3. **EGI Send Event** - sends a single event marker (4-character **Event
   type**, plus optional label/description/extra data). **Event duration** defaults
   to `0.1` seconds. With **Sync to screen refresh** on (the default) the marker is
   sent from `win.callOnFlip()`, so it is timestamped to the flip which actually
   showed the stimulus. Its optional **Target visual Component** field accepts
   the exact Name of a visual Component and binds to its first drawing flip;
   place the marker below that target in the Routine.

Configure network, endian, drift, and diagnostic settings on the EGI NetStation
Device Manager entry. Each active Component's **Device** field selects that
entry. Multiple Components may share the device while retaining independent
Builder lifecycle state. If a selected device is missing, the generated script
raises a clear `ValueError` during setup.

### Drift correction

Device Manager's **Drift correction** setting has two modes:

| Mode | You must | Forgetting to wire it up |
|---|---|---|
| **Background thread** | nothing | cannot happen |
| **Off** | nothing | n/a |

Background sampling is the upstream default because it keeps drift correction alive
without asking the experiment to provide inter-trial sampling windows. Advanced
cooperative/manual drift methods still exist on the Python wrapper for custom code, but
they are no longer exposed as Builder buttons.

The optional **Enable drift warmup** checkbox builds a provisional model during
the first 20 seconds after connecting. It is off by default; enable it when a
timing test shows unstable drift near the start of a recording. The ordinary
drift model takes over automatically once it has enough samples.

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

EGI Start Recording's **Display** tab has two settings:

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
flip-synced markers safe. A failed send therefore cannot raise into experiment
code. Cleanup reports both asynchronous worker failures and ECI responses that
the amplifier rejected or returned malformed. `sessionSummary()` combines
those results with drift and NTP health; `eventErrors()` and `eciErrors()`
provide the underlying failure lists.

For diagnostic sessions, Device Manager's **Strict ECI responses** option makes
failed responses raise from blocking calls. Asynchronous callbacks still
cannot raise into the experiment thread, so their failures remain available in
the cleanup report.

## Troubleshooting

- **No EGI NetStation option appears in Device Manager:** restart PsychoPy after
  installing the plugin. The backend offers a manual profile because the
  amplifier cannot be discovered automatically.
- **The EGI Components do not appear:** confirm the plugin is installed into
  PsychoPy's Python environment, then restart PsychoPy.
- **Connection refused or times out:** confirm ECI is enabled, the host IP and
  port are correct, both computers can reach each other, and local firewall
  rules allow the connection.
- **No event markers arrive:** start recording before sending events and inspect
  the experiment log for asynchronous worker failures and rejected ECI
  responses.
- **Clock synchronization fails:** confirm the amplifier NTP IP is reachable
  from the experiment computer.

## Documentation

The complete documentation includes a tab-by-tab reference for every Builder
Component option, a guided experiment setup, the Python API, display-timing
guidance, and troubleshooting. Build it locally with:

```bash
python -m pip install -e ".[docs]"
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser after the build completes.

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
