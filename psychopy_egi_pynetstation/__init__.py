"""
PsychoPy plugin for EGI/Magstim NetStation EEG amplifiers.

Wraps the `egi-pynetstation <https://github.com/nimh-sfim/egi-pynetstation>`_
package so that a NetStation amplifier can be used as a PsychoPy hardware
device (via `psychopy.hardware.DeviceManager`).

``EGINetStation`` is exposed lazily so package metadata and timing helpers can
still be imported in environments where PsychoPy itself is not installed.
"""

__version__ = "0.1.0"

__all__ = ["EGINetStation", "__version__"]


def __getattr__(name):
    if name == "EGINetStation":
        from psychopy_egi_pynetstation.hardware.netstation import EGINetStation

        return EGINetStation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
