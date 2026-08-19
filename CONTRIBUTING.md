# Contributing

Thank you for helping improve PsychoPy EGI NetStation. Bug reports, hardware
validation results, documentation corrections, and code contributions are all
welcome through the project's
[GitHub issue tracker](https://github.com/pmolfese/psychopy-egi-pynetstation/issues).

## Development setup

Create and activate a Python 3.10-or-newer virtual environment, then install the
project and test dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install --editable ".[tests]"
python -m pytest
```

The full Builder tests require PsychoPy. Tests which do not require PsychoPy or
a live amplifier can be run with a lighter installation:

```bash
python -m pip install --editable . pytest
python -m pytest
```

Those runs intentionally report the PsychoPy-dependent modules as skipped.

## Pull requests

Before opening a pull request:

1. Add or update tests for behavior changes.
2. Run the test suite on a supported Python version.
3. Build and inspect the release artifacts:

   ```bash
   python -m pip install build twine
   python -m build
   python -m twine check --strict dist/*
   ```

4. Update `README.md` for user-visible changes and `CHANGELOG.md` for notable
   changes.
5. Do not commit experiment data, participant information, credentials,
   machine-specific settings, or generated build/test artifacts.

## Hardware validation

Changes that affect connection, recording, synchronization, or event sending
should be checked against a physical or simulated NetStation setup when one is
available. Record the following in the issue or pull request:

- operating system, Python version, PsychoPy version, plugin version, and
  `egi-pynetstation` version;
- whether connect, start recording, event sending, stop recording, and
  disconnect all completed successfully;
- whether a flip-synchronized four-character test event appeared in NetStation
  with the expected 0.1-second duration;
- whether `eventErrors()` was empty after queued events were flushed; and
- any relevant ECI or PsychoPy log messages, with sensitive paths and network
  details removed.

Never test unreviewed changes during production data collection.

## Preparing a release

1. Replace `forthcoming` in `CHANGELOG.md` with the release date.
2. Confirm that `pyproject.toml`, `psychopy_egi_pynetstation.__version__`, and
   the GitHub tag all contain the same version.
3. Confirm CI is green and install the built wheel in a clean PsychoPy
   environment.
4. Create a GitHub environment named `pypi`.
5. Configure a PyPI Trusted Publisher for owner `pmolfese`, repository
   `psychopy-egi-pynetstation`, workflow `pypi.yml`, and environment `pypi`.
6. Publish a GitHub Release tagged `v0.1.0`. The publishing workflow validates
   the tag, builds the distributions, and uploads them to PyPI without an API
   token.

