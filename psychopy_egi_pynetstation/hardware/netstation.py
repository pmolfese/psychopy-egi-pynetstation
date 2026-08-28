"""
PsychoPy hardware device wrapping `egi_pynetstation.NetStation`, so an
EGI/Magstim NetStation amplifier can be used via
`psychopy.hardware.DeviceManager`.

Targets egi-pynetstation >= 2.1.0.
"""

from psychopy.hardware.base import BaseDevice
from psychopy import logging

from egi_pynetstation import NetStation


DEFAULT_NETSTATION_IP = "10.10.10.42"
DEFAULT_AMP_IP = "10.10.10.51"
DEFAULT_PORT = 55513


class EGINetStation(BaseDevice, aliases=["egi_netstation", "netstation"]):
    """
    Interface for an EGI/Magstim NetStation EEG amplifier, via the NetStation
    ECI protocol (`egi-pynetstation
    <https://github.com/nimh-sfim/egi-pynetstation>`_).

    Parameters
    ----------
    ip : str
        IP address of the NetStation host computer. Defaults to
        "10.10.10.42".
    port : int
        Port NetStation's ECI server is listening on (usually 55513).
    ntpIP : str
        IP address of the NTP server running on the amplifier. Defaults to
        "10.10.10.51"; pass None to use `ip`.
    endian : str
        ECI byte-order option for this computer. Use "NTEL" for
        little-endian systems: modern Intel Macs, Apple Silicon Macs,
        Windows x86/x64, and most ARM64 Linux. "MAC-" is for legacy
        PowerPC-era Macs. "UNIX" is big-endian and only appropriate for
        legacy big-endian Unix systems; the name is misleading for most
        modern Unix/Linux computers. Default is "NTEL".
    driftCorrection : bool
        Enable client-side drift correction for `getTime()`.
    autoDrift : bool
        Enable automatic drift sampling. With the default
        `autoDriftBackground=True`, the package samples on its own thread.
    autoDriftInterval : float
        Target seconds between drift samples.
    autoDriftMinPause : float
        Minimum idle time a caller must be able to offer before
        `sampleDriftIfDue()` will take a cooperative sample. Unused in
        background mode.
    autoDriftBackground : bool
        If True, the package samples drift on its own thread and nothing
        else is required. If False, sampling is cooperative and experiment
        code must call `sampleDriftIfDue()`.
    debug : bool
        If True, print ECI command and response bytes.
    errorLog : str
        Optional path for a JSON-lines log of ECI errors.
    strictECI : bool
        If True, rejected or malformed ECI responses raise from blocking
        calls. Asynchronous event sends still cannot raise into experiment
        code; their failures are collected for end-of-session reporting.

    Notes
    -----
    Event sending is always asynchronous in egi-pynetstation >= 2.0.0:
    `sendEvent()` captures its timestamp on the calling thread and returns
    in microseconds, which is what makes it safe inside `win.callOnFlip()`.
    Because a failed send can't raise into experiment code, failures are
    collected - check `sessionSummary()` at the end of a run.

    Examples
    --------
    ::

        from psychopy.hardware import DeviceManager

        ns = DeviceManager.addDevice(
            deviceClass="psychopy_egi_pynetstation.hardware.netstation.EGINetStation",
            deviceName="netstation",
            ip="10.10.10.42",
            ntpIP="10.10.10.51",
        )
        ns.connect()          # applies the drift settings given above
        ns.beginRecording()

        # mark stimulus onset on the flip that actually shows it
        win.callOnFlip(ns.sendEvent, eventType="stim", label="face")
        win.flip()

        ns.endRecording()
        ns.disconnect()
    """

    def __init__(
        self,
        ip=DEFAULT_NETSTATION_IP,
        port=DEFAULT_PORT,
        ntpIP=DEFAULT_AMP_IP,
        endian="NTEL",
        driftCorrection=True,
        autoDrift=True,
        autoDriftInterval=15.0,
        autoDriftMinPause=0.35,
        autoDriftBackground=True,
        debug=False,
        errorLog=None,
        strictECI=False,
    ):
        self.ip = ip
        # PsychoPy's numeric Builder params can arrive as floats (for example
        # 55513.0), while the socket API requires an integer port.
        self.port = int(port)
        self.ntpIP = ntpIP or ip
        self.endian = endian
        self.driftCorrection = driftCorrection
        self.autoDrift = autoDrift
        self.autoDriftInterval = autoDriftInterval
        self.autoDriftMinPause = autoDriftMinPause
        self.autoDriftBackground = autoDriftBackground
        self.strictECI = strictECI
        self._connected = False
        self._recording = False
        self._sessionStarted = False
        self._sessionRecorded = False
        self._sessionReported = True
        self._netstation = NetStation(
            ip, self.port, endian=endian, debug=debug, error_log=errorLog
        )

    # --- connection ---

    def connect(self, clock="ntp"):
        """
        Open the TCP/IP connection to NetStation, applying the drift
        settings this device was created with.

        Parameters
        ----------
        clock : str
            Clock sync method. Only "ntp" is implemented upstream.
        """
        self._netstation.connect(
            clock=clock,
            ntp_ip=self.ntpIP,
            drift_correction=self.driftCorrection,
            auto_drift=self.autoDrift,
            auto_drift_interval=self.autoDriftInterval,
            auto_drift_min_pause=self.autoDriftMinPause,
            auto_drift_background=self.autoDriftBackground,
            strict_eci=self.strictECI,
        )
        self._connected = True
        self._sessionStarted = True
        self._sessionRecorded = False
        self._sessionReported = False
        logging.info(f"Connected to NetStation at {self.ip}:{self.port}")

    def disconnect(self):
        """
        Close the TCP/IP connection. Any queued asynchronous events are
        flushed first.
        """
        self._netstation.disconnect()
        self._connected = False
        self._recording = False
        self._reportSession()

    # --- recording ---

    def beginRecording(self):
        """
        Start EEG recording. This also performs the ECI NTP sync which
        establishes the event timestamp epoch, so it requires an NTP IP.
        """
        self._netstation.begin_rec()
        self._recording = True
        self._sessionRecorded = True

    def endRecording(self):
        """
        Stop EEG recording. Any queued asynchronous events are flushed
        first, so markers sent just beforehand still arrive.
        """
        self._netstation.end_rec()
        self._recording = False

    def close(self):
        """
        Safely finish recording, flush events, and close the connection.

        This is idempotent and is registered as an experiment-exit callback by
        the Builder Component. Explicit Stop Recording and Disconnect Components
        remain useful for choosing the precise endpoint; this method is the safety
        net for normal completion, Escape, and partially configured experiments.
        Cleanup failures are logged rather than masking experiment shutdown.
        """
        if self._connected and self._recording:
            try:
                self.endRecording()
            except Exception as err:
                logging.error(f"Could not stop NetStation recording: {err}")

        if self._connected:
            try:
                self.disconnect()
            except Exception as err:
                logging.error(f"Could not disconnect from NetStation: {err}")

        self._reportSession()

    def _reportSession(self):
        """Log one complete health report for the current connection."""
        if not self._sessionStarted or self._sessionReported:
            return

        try:
            eventErrors = self.eventErrors()
            eciErrors = self.eciErrors()
            summary = self.sessionSummary()
        except Exception as err:
            logging.warning(f"Could not inspect NetStation session health: {err}")
            return
        self._sessionReported = True

        logging.info(f"NetStation session summary: {summary}")

        if eventErrors:
            logging.error(
                f"{len(eventErrors)} NetStation asynchronous event sends failed: "
                f"{eventErrors[:3]}"
            )
        eciErrorCount = summary.get("eci_response_failures", len(eciErrors))
        if eciErrorCount:
            logging.error(
                f"{eciErrorCount} NetStation ECI responses failed: "
                f"{eciErrors[:3]}"
            )

        if not self._sessionRecorded or not self.driftCorrection:
            return
        if summary.get("drift_stalled"):
            logging.error("NetStation drift correction stalled during the session.")
        if summary.get("ntp_sampling_stale"):
            logging.error("NetStation NTP drift sampling was stale at session end.")
        elif not summary.get("drift_engaged"):
            logging.warning(
                "NetStation drift correction did not collect enough history to "
                "engage during this session."
            )
        if summary.get("ntp_sample_failures"):
            logging.warning(
                f"NetStation recorded {summary['ntp_sample_failures']} failed "
                "NTP drift sample requests during the session."
            )

    # --- events ---

    def sendEvent(
        self,
        eventType,
        start="now",
        duration=0.1,
        label=None,
        desc="",
        data=None,
        wait=False,
    ):
        """
        Send an event marker to NetStation.

        In async mode (the default) this captures the timestamp and returns
        in microseconds, so it is safe to pass to `win.callOnFlip()`.

        Parameters
        ----------
        eventType : str
            Exactly 4 characters identifying the type of event, e.g.
            "stim" or "resp". This is the main identifier NetStation uses.
        start : str or float
            "now" to timestamp using the current time, or a float giving
            seconds since recording started.
        duration : float
            Duration of the event in seconds. Default 0.1; the minimum is
            0.001.
        label : str
            Up to 256 characters describing the event. Defaults to
            `eventType` if not given.
        desc : str
            Up to 256 characters with further description of the event.
        data : dict
            Extra key/value data to attach to the event. Keys must be
            exactly 4 characters; values must be str, bool, int or float.
        wait : bool
            Whether to block until the amplifier replies. False is the
            normal, flip-safe default.
        """
        return self._netstation.send_event(
            start=start,
            duration=duration,
            event_type=eventType,
            label=label if label is not None else eventType,
            desc=desc,
            data=data or {},
            wait=wait,
        )

    def flushEvents(self, timeout=None):
        """
        Block until every queued asynchronous event has been sent. Called
        automatically by `endRecording()` and `disconnect()`.
        """
        return self._netstation.flush_events(timeout=timeout)

    def pendingEvents(self):
        """
        How many asynchronous events are still waiting to be sent. A value
        which grows without bound means the sender can't keep up.
        """
        return self._netstation.pending_events()

    def eventErrors(self):
        """
        Exceptions raised by the asynchronous event worker. Rejected or
        malformed amplifier responses are reported separately by
        `eciErrors()`. With strict handling enabled, the same response can
        also appear here because it raised in the worker.
        """
        return self._netstation.event_errors()

    def eciErrors(self):
        """
        Rejected or malformed ECI responses recorded instead of raised.
        """
        return self._netstation.eci_errors()

    def sessionSummary(self):
        """
        One-call summary of event delivery, ECI responses, and clock health.
        """
        return self._netstation.session_summary()

    def setStrictECI(self, enabled=True):
        """
        Choose whether failed ECI responses raise from blocking calls.

        Asynchronous sends cannot raise into experiment code. With strict
        handling enabled, those response failures are also collected by
        `eventErrors()` when they raise in the worker.
        """
        self.strictECI = self._netstation.set_strict_eci(enabled=enabled)
        return self.strictECI

    # --- clock / drift ---

    def resync(self):
        """
        Deprecated diagnostic alias for upstream `sync_return_clock()`.

        Background drift sampling keeps the timestamp model current during
        normal experiments. This method may raise while background sampling
        is active, and can write diagnostic `resy` markers when it does run.
        """
        return self._netstation.resync()

    def configureAutoDrift(
        self, enabled=True, interval=None, min_pause=None, background=None
    ):
        """
        Configure the schedule used by `sampleDriftIfDue()`.

        Parameters
        ----------
        enabled : bool
            Whether `sampleDriftIfDue()` may take samples at all.
        interval : float
            Target seconds between drift samples.
        min_pause : float
            Minimum idle time, in seconds, the experiment must be able to
            offer before a sample is taken.
        background : bool
            Whether sampling should be handled by the package's background
            thread. True is the normal experiment default.
        """
        return self._netstation.configure_auto_drift(
            enabled=enabled,
            interval=interval,
            min_pause=min_pause,
            background=background,
        )

    def sampleDriftIfDue(self, availablePause=None):
        """
        Take a drift sample, but only if one is due and there is time for
        it. Call this from an inter-trial interval, passing how much idle
        time is safely available. Pass None to skip the length check.

        Returns
        -------
        dict
            Describes whether a sample was taken, and if not, why not.
        """
        return self._netstation.sample_drift_if_due(
            available_pause=availablePause
        )

    def sampleDrift(self, samples=None, spacing=None):
        """
        Query the NTP server and record a drift sample unconditionally,
        ignoring the schedule.

        This blocks for roughly 170 ms at default settings, so only call it
        from a point you know is safe - never near a screen flip. Prefer
        `sampleDriftIfDue()` unless you are managing the schedule yourself.

        Drift samples are NTP queries only: they send no ECI clock-sync
        command and create no markers in the recording.
        """
        return self._netstation.sample_drift(samples=samples, spacing=spacing)

    def waitForDrift(
        self, timeout=300.0, poll=1.0, onWait=None, **readyOptions
    ):
        """
        Wait until the upstream drift model reports it is ready.

        Call this after `beginRecording()` and before the first timing-critical
        marker when a session should not proceed until drift correction has
        enough clean NTP history. It may block for several minutes, so use it
        during setup or a deliberate pre-run pause, never near a screen flip.

        Parameters
        ----------
        timeout : float
            Maximum seconds to wait.
        poll : float
            Seconds between readiness checks.
        onWait : callable
            Optional callback invoked by upstream while waiting.
        **readyOptions
            Readiness thresholds passed through to upstream.
        """
        return self.wait_for_drift(
            timeout=timeout,
            poll=poll,
            on_wait=onWait,
            **readyOptions,
        )

    def wait_for_drift(
        self, timeout=300.0, poll=1.0, on_wait=None, **ready_options
    ):
        """
        Pythonic alias for `waitForDrift()`, matching upstream naming.
        """
        return self._netstation.wait_for_drift(
            timeout=timeout,
            poll=poll,
            on_wait=on_wait,
            **ready_options,
        )

    def driftEstimate(self):
        """
        Current drift model estimate, as a dict.
        """
        return self._netstation.drift_estimate()

    def driftSettings(self):
        """
        Every drift setting currently in effect, as a dict.
        """
        return self._netstation.drift_settings()

    def clockState(self):
        """
        Current client/server clock synchronization state, as a dict.
        """
        return self._netstation.clock_state()

    def getTime(self):
        """
        Current time according to NetStation's synced (and, once the model
        is live, drift-corrected) clock, in seconds.

        Don't call this from a screen-flip callback - it builds a
        diagnostic snapshot. Use it between trials.
        """
        return self._netstation.getTime()

    # --- diagnostics ---

    def logRecord(self, record):
        """
        Append one arbitrary record to the ECI JSON-lines error log, if a log
        path was configured.

        Uses a private upstream helper, so it degrades to a no-op rather than
        raising if that helper ever goes away. Returns True if written.
        """
        append = getattr(self._netstation, "_append_error_log", None)
        if append is None:
            logging.warning(
                "This egi-pynetstation build has no _append_error_log; "
                "skipping diagnostic record."
            )
            return False
        try:
            append(dict(record))
        except Exception as err:
            logging.warning(f"Could not write diagnostic record: {err}")
            return False
        return True

    def logDisplayTiming(self, fps, framePeriod, source, **extra):
        """
        Record the measured display refresh alongside the recording.

        This is diagnostic only - it does not change any timing. Its value is
        that a one-frame presentation step becomes explicable after the fact
        instead of looking like a marker-timing bug.
        """
        record = {
            "record": "display_timing",
            "measured_fps": fps,
            "frame_period": framePeriod,
            "fps_source": source,
        }
        record.update(extra)
        return self.logRecord(record)

    def timeAtMonotonic(self, monotonicTime):
        """
        Convert a raw `time.monotonic()` reading into an event timestamp.

        For frameworks without a flip callback: capture `time.monotonic()`
        at the critical moment (cheap - no locks, no model work), then
        convert it afterwards::

            captured = time.monotonic()
            # ... once the frame has appeared ...
            ns.sendEvent(eventType="stim", start=ns.timeAtMonotonic(captured))

        In PsychoPy you normally want `win.callOnFlip(ns.sendEvent, ...)`
        instead, which does this for you.
        """
        return self._netstation.time_at_monotonic(monotonicTime)

    # --- DeviceManager plumbing ---

    def isSameDevice(self, other):
        """
        Query whether `other` refers to the same physical amplifier as
        this object, based on IP address and port.
        """
        if isinstance(other, EGINetStation):
            other = {"ip": other.ip, "port": other.port}
        if isinstance(other, dict):
            return (
                self.ip == other.get("ip", None)
                and self.port == other.get("port", self.port)
            )
        return False

    @staticmethod
    def getAvailableDevices():
        """
        NetStation amplifiers can't be auto-discovered on the network, so
        this always returns an empty list. Specify `ip` (and, if needed,
        `port`) directly when creating an EGINetStation device.
        """
        return []
