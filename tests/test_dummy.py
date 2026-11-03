"""Offline backend coverage, also runnable without PsychoPy installed."""

import pytest

from psychopy_egi_pynetstation.hardware._dummy import DummyNetStation


def test_offline_session_and_clock(monkeypatch):
    monkeypatch.setattr('psychopy_egi_pynetstation.hardware._dummy.time.monotonic', lambda: 100.0)
    ns = DummyNetStation()
    ns.connect()
    ns.begin_rec()
    assert ns.time_at_capture(100.25) == 0.25
    assert ns.time_at_monotonic(100.5) == 0.5
    assert ns.getTime() == 0
    ns.send_event(event_type='stim', label='face', data={'cond': 1})
    ns.send_event(event_type='resp', start=0.1, wait=True)
    assert ns.flush_events(timeout=0)
    assert ns.pending_events() == 0
    assert ns.event_errors() == ns.eci_errors() == []
    ns.end_rec()
    ns.disconnect()
    summary = ns.session_summary()
    assert summary['simulated_events'] == 2
    assert summary['events_sent'] == 0
    assert summary['dummy_mode']
    ns.connect()
    assert ns.session_summary()['simulated_events'] == 0
    with pytest.raises(RuntimeError):
        ns.getTime()


@pytest.mark.parametrize('kwargs', [
    {'event_type': 'toolong'}, {'data': {'bad': 1}},
    {'data': {'good': []}}, {'duration': -1}, {'start': 'later'},
])
def test_invalid_events_do_not_count(kwargs):
    ns = DummyNetStation()
    ns.connect()
    ns.begin_rec()
    with pytest.raises((TypeError, ValueError)):
        ns.send_event(**kwargs)
    assert ns.session_summary()['simulated_events'] == 0


def test_drift_operations_are_explicitly_skipped():
    ns = DummyNetStation()
    def unexpected_wait(*args):
        pytest.fail('Dummy drift wait must not poll')
    assert ns.wait_for_drift(on_wait=unexpected_wait)['skipped']
    for result in (ns.resync(), ns.sample_drift(), ns.sample_drift_if_due(), ns.drift_estimate()):
        assert result['reason'] == 'dummy_mode'
        assert not result['ready']
    assert not ns.configure_auto_drift(enabled=True, background=True)['auto_drift']
    assert not ns.clock_state()['synchronized']
