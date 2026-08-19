"""
Display frame-beat helpers.

A display refreshes on a fixed heartbeat; an experiment asks for stimuli on its
own schedule. When an inter-stimulus interval is not a whole number of refresh
periods, the request creeps through the refresh cycle a little each trial. The
creep itself is harmless, but a display can only present at a frame boundary,
so the outcome is binary - the request either makes this frame or waits for the
next. The creep therefore surfaces as a sudden one-frame step.

None of this is visible to egi-pynetstation: the package never sees a frame,
and event timestamps were never wrong. These helpers exist so the plugin can
*measure and report* the risk. They deliberately do not reschedule anything.

Everything here except `measureDisplay` is pure and importable without
PsychoPy.
"""

from collections import Counter
from collections.abc import Mapping

__all__ = [
    "frameSlip",
    "beatSeconds",
    "framesFor",
    "measureDisplay",
    "describeSchedule",
]

# Slip below this is treated as an exact whole number of frames. Floating point
# noise on a division is many orders of magnitude smaller than a real 7 ppm
# display offset, so this cleanly separates "no beat" from "a very slow beat".
SLIP_TOLERANCE = 1e-9


def frameSlip(interval, framePeriod):
    """
    Fractional frames by which `interval` misses a whole number of frames.

    Parameters
    ----------
    interval : float
        Interval in seconds, e.g. an inter-stimulus interval.
    framePeriod : float
        Seconds per display refresh.

    Returns
    -------
    float
        Between 0 and 0.5. Zero means the interval is an exact whole number
        of frames and there is no beat.
    """
    if framePeriod <= 0:
        raise ValueError(f"framePeriod must be positive, got {framePeriod}")
    frames = interval / framePeriod
    return abs(frames - round(frames))


def beatSeconds(interval, framePeriod, tolerance=SLIP_TOLERANCE):
    """
    Seconds for the onset phase to sweep one whole frame.

    This is how long a run can go before the accumulated creep produces a
    one-frame step in stimulus presentation.

    Returns
    -------
    float or None
        None when the interval is a whole number of frames (no beat).
    """
    slip = frameSlip(interval, framePeriod)
    if slip <= tolerance:
        return None
    return interval / slip


def framesFor(interval, framePeriod):
    """
    Whole frames closest to `interval`, for frame-counted scheduling.

    Never returns less than 1 - an interval shorter than a frame still needs
    a frame to be shown in.
    """
    if framePeriod <= 0:
        raise ValueError(f"framePeriod must be positive, got {framePeriod}")
    return max(1, int(round(interval / framePeriod)))


def measureDisplay(
    win,
    nIdentical=10,
    nMaxFrames=240,
    nWarmUpFrames=20,
    threshold=1,
):
    """
    Measure the real refresh rate, falling back progressively.

    The whole effect is invisible at exactly 60.000 Hz, where every common
    interval is a whole number of frames - so the measured value is what makes
    the problem detectable at all. Never assume 60.

    This takes 1-2 seconds and drops frames. Call it at setup only, never
    anywhere timing-critical.

    Returns
    -------
    (fps, framePeriod, source)
        `source` is "measured", "reported" (from the monitor configuration) or
        "assumed" (60 Hz - treat any result derived from this with suspicion).
    """
    measured = None
    try:
        measured = win.getActualFrameRate(
            nIdentical=nIdentical,
            nMaxFrames=nMaxFrames,
            nWarmUpFrames=nWarmUpFrames,
            threshold=threshold,
        )
    except Exception:
        measured = None

    if measured:
        measured = float(measured)
        return measured, 1.0 / measured, "measured"

    reported = getattr(win, "monitorFramePeriod", None)
    if reported:
        reported = float(reported)
        return 1.0 / reported, reported, "reported"

    return 60.0, 1.0 / 60.0, "assumed"


def _weighted(intervals):
    """
    Normalise `intervals` to {interval: weight}.

    Accepts a mapping of interval to weight, or a sequence in which each
    occurrence counts once.
    """
    if isinstance(intervals, Mapping):
        return {float(k): float(v) for k, v in intervals.items() if v > 0}
    return {float(k): float(v) for k, v in Counter(intervals).items()}


def describeSchedule(intervals, framePeriod, tolerance=SLIP_TOLERANCE):
    """
    Assess a set of intervals against a frame period.

    The beat is reported for the interval most trials actually use, not the
    one with the worst rounding. Taking the worst badly overstates the risk
    whenever one interval dominates the design - a run of 1235 trials in which
    1153 were 3.0 s is driven by the 3.0 s beat, not by a rare outlier. The
    worst case is still reported, separately and labelled as such.

    Parameters
    ----------
    intervals : mapping or sequence
        Intervals in seconds. A mapping gives explicit weights (e.g. trial
        counts); a sequence counts each occurrence once.
    framePeriod : float
        Seconds per display refresh.

    Returns
    -------
    dict
        With keys `modal`, `worst` and `messages`. `modal` and `worst` are
        None when there is nothing to report. `messages` is a list of
        human-readable lines, empty when no interval beats.
    """
    weights = _weighted(intervals)
    if not weights or framePeriod <= 0:
        return {"modal": None, "worst": None, "messages": []}

    def entry(interval):
        slip = frameSlip(interval, framePeriod)
        return {
            "interval": interval,
            "weight": weights[interval],
            "frames": interval / framePeriod,
            "slip": slip,
            "beatSeconds": (
                None if slip <= tolerance else interval / slip
            ),
        }

    # the interval most trials actually use - ties broken toward the longer
    # interval so the reported beat is the conservative one
    modalInterval = max(weights, key=lambda i: (weights[i], i))
    modal = entry(modalInterval)
    worst = entry(max(weights, key=lambda i: frameSlip(i, framePeriod)))

    messages = []
    if modal["beatSeconds"] is not None:
        messages.append(
            "{interval:g} s is {slip:.5f} frame off a whole number at "
            "{fps:.4f} Hz. Under clock timing the stimulus onset phase sweeps "
            "a full frame about every {beat:.0f} min, which can produce a "
            "one-frame ({frameMs:.1f} ms) step in stimulus presentation. "
            "Consider specifying durations in frames.".format(
                interval=modal["interval"],
                slip=modal["slip"],
                fps=1.0 / framePeriod,
                beat=modal["beatSeconds"] / 60.0,
                frameMs=framePeriod * 1000.0,
            )
        )
        if worst["interval"] != modal["interval"]:
            messages.append(
                "Worst interval rounding is {worstSlip:.5f} frame at "
                "{worstInterval:g} s; the beat above is for the interval most "
                "trials use.".format(
                    worstSlip=worst["slip"],
                    worstInterval=worst["interval"],
                )
            )

    return {"modal": modal, "worst": worst, "messages": messages}
