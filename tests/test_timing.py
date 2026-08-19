"""
Tests for the display frame-beat helpers.

These are pure functions and need no PsychoPy, no window and no amplifier.
The worked numbers come from a real one-hour photocell validation run on a
display measured at 60.00043 Hz.
"""
import pytest

from psychopy_egi_pynetstation.timing import (
    beatSeconds,
    describeSchedule,
    frameSlip,
    framesFor,
    measureDisplay,
)


# the measured display from the validation run: 7 ppm fast
MEASURED_FPS = 60.00043
MEASURED_PERIOD = 1.0 / MEASURED_FPS


class FakeWindow:
    def __init__(self, fps=None, monitorFramePeriod=None, raises=False):
        self._fps = fps
        self._raises = raises
        if monitorFramePeriod is not None:
            self.monitorFramePeriod = monitorFramePeriod

    def getActualFrameRate(self, **kwargs):
        if self._raises:
            raise RuntimeError("no display")
        return self._fps


# --- the worked example from the validation run ---


def test_frame_period_matches_measurement():
    assert MEASURED_PERIOD * 1000 == pytest.approx(16.6665, abs=1e-4)


def test_three_second_isi_slip():
    slip = frameSlip(3.0, MEASURED_PERIOD)
    assert slip == pytest.approx(0.00129, abs=1e-5)
    # about 22 microseconds of creep per trial
    assert slip * MEASURED_PERIOD == pytest.approx(21.5e-6, abs=2e-6)


def test_three_second_isi_beat_period():
    # the run showed steps 40.8 min apart against a ~39 min prediction
    beat = beatSeconds(3.0, MEASURED_PERIOD)
    assert beat / 60.0 == pytest.approx(39, abs=1.0)


def test_frames_for_rounds_to_whole_frames():
    assert framesFor(3.0, MEASURED_PERIOD) == 180
    # an interval shorter than a frame still needs one frame to be shown in
    assert framesFor(0.001, MEASURED_PERIOD) == 1


# --- the effect is invisible at exactly 60 Hz ---


@pytest.mark.parametrize("isi", [0.5, 1.0, 2.0, 3.0])
def test_no_beat_at_exactly_sixty_hz(isi):
    """
    Every common interval is a whole number of frames at exactly 60.000 Hz.
    This is why the refresh must be measured rather than assumed - assuming
    60 hides the problem completely.
    """
    assert beatSeconds(isi, 1.0 / 60.0) is None
    assert frameSlip(isi, 1.0 / 60.0) == pytest.approx(0.0, abs=1e-12)


def test_beat_appears_once_the_real_rate_is_used():
    assert beatSeconds(3.0, 1.0 / 60.0) is None
    assert beatSeconds(3.0, MEASURED_PERIOD) is not None


# --- modal vs worst ---


def test_beat_reported_for_modal_not_worst_interval():
    """
    Regression guard. Computing the beat from the worst-rounding interval
    badly overstates it when one interval dominates: in the validation run
    1153 of 1235 trials were 3.0 s, so the 3.0 s beat is the one that
    matters, not that of a rare outlier.
    """
    # a 125 ms stimulus lands on 7.5 frames - the worst possible rounding -
    # but only a handful of trials use it
    schedule = {3.0: 1153, 0.125: 82}
    assert frameSlip(0.125, MEASURED_PERIOD) > frameSlip(3.0, MEASURED_PERIOD)

    result = describeSchedule(schedule, MEASURED_PERIOD)

    assert result["modal"]["interval"] == 3.0
    assert result["modal"]["weight"] == 1153
    assert result["worst"]["interval"] == 0.125
    # the headline beat is the modal one
    assert "3 s" in result["messages"][0]
    assert result["modal"]["beatSeconds"] == pytest.approx(
        beatSeconds(3.0, MEASURED_PERIOD)
    )


def test_worst_is_still_reported_separately():
    result = describeSchedule({3.0: 1153, 0.125: 82}, MEASURED_PERIOD)
    assert any("Worst interval rounding" in m for m in result["messages"])


def test_no_redundant_worst_line_when_worst_is_the_modal_interval():
    # 3.0 s rounds worse than 1.7 s here, so both roles fall to the same
    # interval and the second message would just repeat the first
    result = describeSchedule({3.0: 1153, 1.7: 82}, MEASURED_PERIOD)
    assert result["worst"]["interval"] == result["modal"]["interval"] == 3.0
    assert len(result["messages"]) == 1


def test_sequence_input_counts_occurrences():
    result = describeSchedule([3.0, 3.0, 3.0, 1.7], MEASURED_PERIOD)
    assert result["modal"]["interval"] == 3.0
    assert result["modal"]["weight"] == 3


def test_no_messages_when_schedule_is_whole_frames():
    result = describeSchedule({3.0: 100}, 1.0 / 60.0)
    assert result["messages"] == []
    assert result["modal"]["beatSeconds"] is None


def test_empty_schedule_is_safe():
    result = describeSchedule({}, MEASURED_PERIOD)
    assert result == {"modal": None, "worst": None, "messages": []}


# --- measurement fallback chain ---


def test_measure_prefers_actual_frame_rate():
    fps, period, source = measureDisplay(FakeWindow(fps=MEASURED_FPS))
    assert source == "measured"
    assert fps == pytest.approx(MEASURED_FPS)
    assert period == pytest.approx(MEASURED_PERIOD)


def test_measure_falls_back_to_monitor_config():
    win = FakeWindow(fps=None, monitorFramePeriod=1 / 120.0)
    fps, period, source = measureDisplay(win)
    assert source == "reported"
    assert fps == pytest.approx(120.0)


def test_measure_falls_back_to_sixty_when_nothing_available():
    fps, period, source = measureDisplay(FakeWindow(fps=None))
    assert source == "assumed"
    assert fps == pytest.approx(60.0)


def test_measure_survives_a_raising_window():
    # a failed measurement must not take the experiment down with it
    win = FakeWindow(raises=True, monitorFramePeriod=1 / 144.0)
    fps, period, source = measureDisplay(win)
    assert source == "reported"
    assert fps == pytest.approx(144.0)


# --- input validation ---


@pytest.mark.parametrize("bad", [0, -1.0])
def test_non_positive_frame_period_rejected(bad):
    for func in (frameSlip, framesFor):
        with pytest.raises(ValueError):
            func(3.0, bad)
