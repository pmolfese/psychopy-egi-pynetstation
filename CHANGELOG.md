# Changelog

All notable changes to this project will be documented in this file. The
project uses semantic versioning after the initial `0.x` development series.

## 0.1.2 - 2026-11-04

### Fixed

- Send Event Components now become `FINISHED` after dispatching their marker,
  so they do not keep a Routine running. Flip-synchronized markers finish on
  the sending flip, including markers bound to a visual Component.

## 0.1.1 - 2026-11-03

### Added

- Explicit offline dummy mode in Device Manager, legacy Init, and the Python
  wrapper, with event validation, simulated marker counts, local clocks, and
  immediate drift-wait skipping.
- Optional per-device EEG mode selection in the experiment startup dialog.
- Opt-in connection-failure recovery with Abort, Retry, and Continue without
  EEG choices, safe failed-client cleanup, and requested/effective mode metadata.
- Legacy Connect constructor support for dummy and startup/recovery settings.

## 0.1.0 - 2026-10-09

### Added

- PsychoPy hardware wrapper around `egi-pynetstation>=2.1.0`.
- EGI Start Recording, Send Event, and Stop Recording Components for PsychoPy
  Studio, plus hidden compatibility loaders for the former Connect and
  Disconnect Components.
- An EGI NetStation Device Manager backend which owns connection settings and
  connects the device during generated experiment setup.
- Flip-synchronized asynchronous event markers with a default duration of
  0.1 seconds.
- Background clock-drift sampling and event-send error reporting.
- Optional provisional drift warmup from Device Manager.
- High-resolution ``captureTime()`` / ``timeAtCapture()`` wrappers for the
  upstream Windows-safe timestamp capture API.
- Optional drift-readiness waiting through `waitForDrift()` /
  `wait_for_drift()` and EGI Start Recording's Drift tab.
- Session summaries, ECI-response diagnostics, effective drift-setting
  reports, and optional strict ECI response handling.
- Display refresh measurement and warnings for frame-beat-prone schedules.
- Compatibility tests for the upstream `egi-pynetstation` API and generated
  PsychoPy Builder scripts.
- GitHub Actions for supported-Python tests, full PsychoPy tests, distribution
  checks, and PyPI Trusted Publishing.
- A package-level PNG icon for the PsychoPy plugin catalog.

### Changed

- Component classes and entry points use an `Egi` prefix so PsychoPy Studio's
  ComponentButton title formatter renders their names without splitting the
  acronym as `E GI`.
- EGI Send Event can now bind to a selected visual Component in its Routine
  and queue the marker on that Component's first drawing flip. Unsafe target
  ordering is rejected instead of silently producing a one-frame delay.
- Wheel package discovery is restricted to the plugin namespace, preventing
  generated documentation and build directories from entering release wheels.
- The documentation and README now identify the plugin as an independent,
  community-maintained project with no EGI or Magstim EGI affiliation.
- The timing guide now provides a worked, Builder-specific procedure for
  interpreting frame-beat warnings and converting visual schedules to frames.
- NetStation network configuration now lives in PsychoPy Device Manager, and
  visible Components use Studio's native device selector.
- EGI Send Event's target is plain text rather than a callable-backed dropdown,
  allowing its Component template to serialize and load in PsychoPy Studio.
- Visible Components provide SVG icons for PsychoPy Studio.
- Connection cleanup is owned by Device Manager through ``close()``, with a
  best-effort ``__del__`` fallback.
- Builder Components now keep independent lifecycle state while sharing one
  NetStation connection, so multiple EGI commands in a Routine do not suppress
  one another.
- Blocking connection and recording commands refresh Builder's Routine clocks,
  preventing later commands from being skipped when network setup crosses a
  scheduled onset.
- Normal and early experiment exits safely stop an active recording, flush
  queued events, report asynchronous and ECI-response failures plus drift
  health, and disconnect.

### Known limitations

- End-to-end validation against a physical or simulated NetStation amplifier
  is still in progress.
- NetStation amplifiers are not auto-discovered; users enter the network
  addresses explicitly.
