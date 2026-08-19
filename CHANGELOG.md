# Changelog

All notable changes to this project will be documented in this file. The
project uses semantic versioning after the initial `0.x` development series.

## 0.1.0 - forthcoming

### Added

- PsychoPy hardware wrapper around `egi-pynetstation>=2.0.0`.
- EGI Connect, Start Recording, Send Event, Stop Recording, and Disconnect
  Builder Components.
- Flip-synchronized asynchronous event markers with a default duration of
  0.1 seconds.
- Background clock-drift sampling and event-send error reporting.
- Display refresh measurement and warnings for frame-beat-prone schedules.
- Compatibility tests for the upstream `egi-pynetstation` API and generated
  PsychoPy Builder scripts.
- GitHub Actions for supported-Python tests, full PsychoPy tests, distribution
  checks, and PyPI Trusted Publishing.

### Changed

- NetStation network configuration lives entirely in EGI Connect. The shared
  Device label is plain text and requires no Device Manager configuration.

### Known limitations

- End-to-end validation against a physical or simulated NetStation amplifier
  is still in progress.
- NetStation amplifiers are not auto-discovered; users enter the network
  addresses explicitly.

