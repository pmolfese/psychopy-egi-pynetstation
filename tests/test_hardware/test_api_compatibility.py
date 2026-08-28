"""
Guards against the upstream egi-pynetstation API drifting out from under the
plugin.

The wrapper calls NetStation methods by keyword. If upstream renames or removes
one of those keywords, nothing fails until an experiment actually runs - and
because most of these need a live amplifier, the rest of the test suite won't
catch it either. These tests check the installed package's signatures directly,
so that class of breakage fails loudly at test time instead.
"""
import inspect

import pytest

from egi_pynetstation import NetStation


# every keyword the wrapper passes to each upstream method
REQUIRED_KWARGS = {
    "__init__": {"endian", "debug", "error_log"},
    "connect": {
        "clock", "ntp_ip",
        "drift_correction",
        "auto_drift", "auto_drift_interval",
        "auto_drift_min_pause", "auto_drift_background",
        "strict_eci",
    },
    "send_event": {"start", "duration", "event_type", "label", "desc", "data", "wait"},
    "sample_drift": {"samples", "spacing"},
    "sample_drift_if_due": {"available_pause"},
    "configure_auto_drift": {"enabled", "interval", "min_pause", "background"},
    "set_strict_eci": {"enabled"},
    "wait_for_drift": {"timeout", "poll", "on_wait"},
    "flush_events": {"timeout"},
}

# methods the wrapper calls with no arguments
REQUIRED_METHODS = [
    "disconnect", "begin_rec", "end_rec",
    "pending_events", "event_errors", "eci_errors", "session_summary",
    "resync", "drift_estimate", "drift_settings", "clock_state",
    "getTime", "time_at_monotonic",
]


@pytest.mark.parametrize("method,kwargs", sorted(REQUIRED_KWARGS.items()))
def test_upstream_still_accepts_our_kwargs(method, kwargs):
    func = getattr(NetStation, method, None)
    assert func is not None, f"NetStation.{method}() no longer exists"

    params = inspect.signature(func).parameters
    # **kwargs upstream would accept anything, so only check when it doesn't
    if any(p.kind is p.VAR_KEYWORD for p in params.values()):
        return

    missing = sorted(kwargs - set(params))
    assert not missing, (
        f"NetStation.{method}() no longer accepts {missing}. "
        f"The plugin's wrapper passes these; update "
        f"psychopy_egi_pynetstation/hardware/netstation.py to match."
    )


@pytest.mark.parametrize("method", REQUIRED_METHODS)
def test_upstream_still_provides_method(method):
    assert callable(getattr(NetStation, method, None)), (
        f"NetStation.{method}() no longer exists, but the plugin's wrapper "
        f"calls it."
    )


def test_async_send_is_not_reconfigurable():
    """
    Event sending became unconditionally asynchronous, with `wait=True` as the
    per-call opt-out. If an `async_events`-style connect flag ever comes back,
    the wrapper should be revisited rather than silently ignoring it.
    """
    params = inspect.signature(NetStation.connect).parameters
    assert "async_events" not in params, (
        "connect() accepts `async_events` again - revisit whether the plugin "
        "should be setting it."
    )
    assert "wait" in inspect.signature(NetStation.send_event).parameters
