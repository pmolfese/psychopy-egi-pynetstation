"""Offline NetStation backend: no sockets, threads, or hardware timestamps."""

import time

from egi_pynetstation.eci import package_event
from egi_pynetstation.exceptions import NetStationUnconnected


class DummyNetStation:
    """Implement the client operations used by EGINetStation for rehearsal."""

    def __init__(self):
        self.connected = False
        self.recording = False
        self._epoch = None
        self._events = 0
        self._strict = False

    def _require_connection(self):
        if not self.connected:
            raise NetStationUnconnected()

    def connect(self, **settings):
        self.connected = True
        self.recording = False
        self._epoch = None
        self._events = 0
        self._strict = settings.get('strict_eci', False)

    def disconnect(self):
        self.connected = False
        self.recording = False

    def begin_rec(self):
        self._require_connection()
        if not self.recording:
            self._epoch = time.monotonic()
        self.recording = True

    def end_rec(self):
        self._require_connection()
        self.recording = False

    def send_event(self, start='now', duration=0.1, event_type='stim',
                   label=None, desc='', data=None, wait=False):
        self._require_connection()
        if not self.recording:
            raise RuntimeError('Dummy NetStation events require recording to start')
        if start == 'now':
            start = self.getTime()
        elif not isinstance(start, (int, float)):
            raise TypeError('Start must be "now" or a number of seconds')
        # Reuse upstream's pure serializer to validate the real event format.
        # Nothing is retained or sent, including when wait=True.
        package_event(
            start, duration, event_type,
            event_type if label is None else label, desc, data or {},
        )
        self._events += 1

    def flush_events(self, timeout=None):
        return True

    def pending_events(self):
        return 0

    def event_errors(self):
        return []

    def eci_errors(self):
        return []

    def session_summary(self):
        return dict(dummy_mode=True, simulated_events=self._events,
                    events_sent=0, eci_response_failures=0,
                    connected=self.connected, recording=self.recording,
                    clock_source='local_monotonic', drift_engaged=False)

    def set_strict_eci(self, enabled=True):
        self._strict = bool(enabled)
        return self._strict

    @staticmethod
    def _skipped():
        return dict(dummy_mode=True, skipped=True, reason='dummy_mode',
                    sampled=False, ready=False)

    def resync(self):
        return self._skipped()

    def configure_auto_drift(self, enabled=True, interval=None,
                             min_pause=None, background=None):
        return self.drift_settings()

    def sample_drift_if_due(self, available_pause=None):
        return self._skipped()

    def sample_drift(self, samples=None, spacing=None):
        return self._skipped()

    def wait_for_drift(self, timeout=300.0, poll=1.0, on_wait=None, **options):
        return self._skipped()

    def drift_estimate(self):
        return self._skipped()

    def drift_settings(self):
        return dict(dummy_mode=True, drift_correction=False,
                    auto_drift=False, auto_drift_background=False)

    def clock_state(self):
        return dict(dummy_mode=True, clock_source='local_monotonic',
                    synchronized=False, recording=self.recording)

    def getTime(self):
        return self.time_at_capture(self.capture_time())

    def capture_time(self):
        return time.monotonic()

    def time_at_capture(self, captured_time):
        if self._epoch is None:
            raise RuntimeError('Dummy clock is unavailable before recording starts')
        return captured_time - self._epoch

    def time_at_monotonic(self, monotonic_time):
        return self.time_at_capture(monotonic_time)
