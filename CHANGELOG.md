# Changelog

All notable changes to this project will be documented in this file. The
project uses semantic versioning after the initial `0.x` development series.

## 0.1.0 - forthcoming

### Added

- PsychoPy hardware wrapper around `egi-pynetstation>=2.1.0`.
- EGI Connect, Start Recording, Send Event, Stop Recording, and Disconnect
  Builder Components.
- Flip-synchronized asynchronous event markers with a default duration of
  0.1 seconds.
- Background clock-drift sampling and event-send error reporting.
- Optional provisional drift warmup from EGI Connect.
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

### Changed

- Builder widget titles now capitalize `EGI` consistently, while the former
  mixed-case component imports remain available as compatibility aliases.
- EGI Send Event can now bind to a selected visual Component in its Routine
  and queue the marker on that Component's first drawing flip. Unsafe target
  ordering is rejected instead of silently producing a one-frame delay.
- Wheel package discovery is restricted to the plugin namespace, preventing
  generated documentation and build directories from entering release wheels.
- The documentation and README now identify the plugin as an independent,
  community-maintained project with no EGI or Magstim EGI affiliation.
- The timing guide now provides a worked, Builder-specific procedure for
  interpreting frame-beat warnings and converting visual schedules to frames,
  with current screenshots of the EGI Send Event target selector.
- NetStation network configuration lives entirely in EGI Connect. The shared
  Device label is plain text and requires no Device Manager configuration.
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
