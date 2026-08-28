import pytest

# the device wrapper subclasses psychopy.hardware.base.BaseDevice
pytest.importorskip("psychopy.hardware.base")

from egi_pynetstation.exceptions import NetStationUnconnected  # noqa: E402

from psychopy_egi_pynetstation.hardware.netstation import EGINetStation  # noqa: E402
from psychopy_egi_pynetstation import EGINetStation as PublicEGINetStation  # noqa: E402


@pytest.fixture
def device():
    # constructing EGINetStation doesn't open a socket, so this is safe
    # without a real amplifier on the network
    return EGINetStation(ip="127.0.0.1", port=55513)


def test_construct_does_not_connect(device):
    assert device._connected is False
    assert device._recording is False
    assert device.ip == "127.0.0.1"
    assert device.port == 55513
    assert device.ntpIP == "10.10.10.51"


def test_wrapper_is_available_from_short_public_import():
    assert PublicEGINetStation is EGINetStation


def test_construct_normalizes_float_port_for_socket():
    device = EGINetStation(ip="127.0.0.1", port=55513.0)

    assert device.port == 55513
    assert isinstance(device.port, int)
    assert device._netstation._socket._address == ("127.0.0.1", 55513)


def test_default_addresses_match_cmn_netstation_setup():
    device = EGINetStation()

    assert device.ip == "10.10.10.42"
    assert device.ntpIP == "10.10.10.51"
    assert device.port == 55513


def test_explicit_none_ntp_ip_falls_back_to_netstation_ip():
    device = EGINetStation(ip="127.0.0.1", ntpIP=None)

    assert device.ntpIP == "127.0.0.1"


def test_is_same_device_dict(device):
    assert device.isSameDevice({"ip": "127.0.0.1", "port": 55513})
    assert not device.isSameDevice({"ip": "10.0.0.1", "port": 55513})
    assert not device.isSameDevice({"ip": "127.0.0.1", "port": 9999})


def test_is_same_device_instance(device):
    other = EGINetStation(ip="127.0.0.1", port=55513)
    assert device.isSameDevice(other)

    other = EGINetStation(ip="10.0.0.1", port=55513)
    assert not device.isSameDevice(other)


def test_is_same_device_rejects_other_types(device):
    assert not device.isSameDevice("not a device")
    assert not device.isSameDevice(None)


def test_get_available_devices_is_empty():
    assert EGINetStation.getAvailableDevices() == []


def test_send_event_requires_connection(device):
    # egi_pynetstation.NetStation.send_event is decorated with
    # @check_connected, so it refuses to run (even to validate its
    # arguments) until connect() has been called
    with pytest.raises(NetStationUnconnected):
        device.sendEvent(eventType="STIM", start=0.0)


def test_send_event_defaults_to_one_tenth_second(device):
    from unittest import mock

    with mock.patch.object(device._netstation, "send_event") as send_event:
        device.sendEvent(eventType="STIM")

    send_event.assert_called_once_with(
        start="now",
        duration=0.1,
        event_type="STIM",
        label="STIM",
        desc="",
        data={},
        wait=False,
    )


# --- egi-pynetstation 2.1.0 surface ---


def test_drift_defaults_are_background(device):
    # upstream now samples drift in the background by default
    assert device.driftCorrection is True
    assert device.autoDrift is True
    assert device.autoDriftBackground is True

    cooperative = EGINetStation(ip="127.0.0.1", autoDriftBackground=False)
    assert cooperative.autoDriftBackground is False


def test_wrapper_defaults_match_upstream_drift_settings(device):
    settings = device.driftSettings()

    assert device.driftCorrection == settings["drift_correction"]
    assert device.autoDrift == settings["auto_drift"]
    assert device.autoDriftInterval == settings["auto_drift_interval"]
    assert device.autoDriftMinPause == settings["auto_drift_min_pause"]
    assert device.autoDriftBackground == settings["auto_drift_background"]


def test_connect_forwards_strict_eci(device):
    from unittest import mock

    device.strictECI = True
    device._sessionRecorded = True
    device._sessionReported = True
    with mock.patch.object(device._netstation, "connect") as connect:
        device.connect()

    assert connect.call_args.kwargs["strict_eci"] is True
    assert device._sessionStarted is True
    assert device._sessionRecorded is False
    assert device._sessionReported is False


@pytest.mark.parametrize("kwargs", [
    {},                                                    # background
    {"autoDriftBackground": False},                        # cooperative
    {"driftCorrection": False, "autoDrift": False},        # off
])
def test_connect_passes_kwargs_upstream_accepts(kwargs):
    """
    connect() is the call that broke when upstream dropped `async_events`, and
    nothing caught it because connecting normally needs an amplifier. Stub the
    socket so the keyword binding itself is exercised.
    """
    from unittest import mock

    dev = EGINetStation(ip="127.0.0.1", ntpIP="127.0.0.1", **kwargs)
    with mock.patch.object(dev._netstation, "_socket"), \
            mock.patch.object(dev._netstation, "_command"):
        try:
            dev.connect()
            assert dev._connected is True
        finally:
            # background mode starts a real thread; don't leak it
            dev._netstation._stop_auto_drift_thread()


def test_event_bookkeeping_works_before_connecting(device):
    # these aren't @check_connected upstream, so they're safe to call at any
    # point - including the end-of-experiment error report
    assert device.eventErrors() == []
    assert device.eciErrors() == []
    assert device.pendingEvents() == 0


def test_diagnostic_wrappers_delegate_upstream(device):
    from unittest import mock

    with mock.patch.object(
        device._netstation, "session_summary", return_value={"ok": True}
    ), mock.patch.object(
        device._netstation, "drift_settings", return_value={"auto_drift": True}
    ), mock.patch.object(
        device._netstation, "set_strict_eci", return_value=True
    ) as set_strict:
        assert device.sessionSummary() == {"ok": True}
        assert device.driftSettings() == {"auto_drift": True}
        assert device.setStrictECI(False) is True

    set_strict.assert_called_once_with(enabled=False)
    assert device.strictECI is True


def test_session_report_includes_eci_failures_once(device):
    from unittest import mock
    import psychopy_egi_pynetstation.hardware.netstation as wrapper_module

    device._sessionStarted = True
    device._sessionRecorded = True
    device._sessionReported = False
    summary = {
        "ok": False,
        "drift_engaged": True,
        "drift_stalled": False,
        "event_send_failures": 0,
        "eci_response_failures": 1,
        "ntp_sampling_stale": False,
        "ntp_sample_failures": 0,
    }
    failure = {"cmd": "EventData", "error": "ECIFailure"}

    with mock.patch.object(device._netstation, "event_errors", return_value=[]), \
            mock.patch.object(
                device._netstation, "eci_errors", return_value=[failure]
            ), mock.patch.object(
                device._netstation, "session_summary", return_value=summary
            ), mock.patch.object(wrapper_module.logging, "error") as log_error:
        device._reportSession()
        device._reportSession()

    assert log_error.call_count == 1
    assert "ECI responses failed" in log_error.call_args.args[0]


def test_drift_disabled_session_does_not_log_health_failure(device):
    from unittest import mock
    import psychopy_egi_pynetstation.hardware.netstation as wrapper_module

    device.driftCorrection = False
    device._sessionStarted = True
    device._sessionRecorded = True
    device._sessionReported = False
    summary = {
        "ok": False,
        "drift_engaged": False,
        "drift_stalled": False,
        "event_send_failures": 0,
        "eci_response_failures": 0,
        "ntp_sampling_stale": True,
        "ntp_sample_failures": 0,
    }

    with mock.patch.object(device._netstation, "event_errors", return_value=[]), \
            mock.patch.object(device._netstation, "eci_errors", return_value=[]), \
            mock.patch.object(
                device._netstation, "session_summary", return_value=summary
            ), mock.patch.object(wrapper_module.logging, "error") as log_error, \
            mock.patch.object(wrapper_module.logging, "warning") as log_warning:
        device._reportSession()

    log_error.assert_not_called()
    log_warning.assert_not_called()


def test_close_stops_recording_then_disconnects(device):
    from unittest import mock

    device._connected = True
    device._recording = True
    calls = []
    with mock.patch.object(
        device._netstation, "end_rec", side_effect=lambda: calls.append("stop")
    ), mock.patch.object(
        device._netstation,
        "disconnect",
        side_effect=lambda: calls.append("disconnect"),
    ):
        device.close()
        device.close()

    assert calls == ["stop", "disconnect"]
    assert device._connected is False
    assert device._recording is False


def test_close_is_safe_before_connecting(device):
    device.close()

    assert device._connected is False
    assert device._recording is False


def test_drift_calls_require_connection(device):
    # both are @check_connected upstream
    with pytest.raises(NetStationUnconnected):
        device.configureAutoDrift(enabled=True, interval=30.0)

    with pytest.raises(NetStationUnconnected):
        device.sampleDriftIfDue(availablePause=1.0)


def test_wait_for_drift_delegates_to_upstream(device):
    from unittest import mock

    with mock.patch.object(
        device._netstation,
        "wait_for_drift",
        create=True,
        return_value={"ready": True},
    ) as wait:
        result = device.waitForDrift(
            timeout=12.0,
            poll=0.5,
            onWait="callback",
            min_samples=4,
        )

    assert result == {"ready": True}
    wait.assert_called_once_with(
        timeout=12.0,
        poll=0.5,
        on_wait="callback",
        min_samples=4,
    )


def test_wait_for_drift_pythonic_alias_delegates_to_upstream(device):
    from unittest import mock

    with mock.patch.object(
        device._netstation,
        "wait_for_drift",
        create=True,
        return_value={"ready": True},
    ) as wait:
        result = device.wait_for_drift(
            timeout=3.0,
            poll=0.25,
            on_wait=None,
            max_delay=0.02,
        )

    assert result == {"ready": True}
    wait.assert_called_once_with(
        timeout=3.0,
        poll=0.25,
        on_wait=None,
        max_delay=0.02,
    )


def test_wrapper_exposes_expected_api():
    # guard against silently losing a method the Builder Components call
    for name in (
        "connect", "disconnect", "close",
        "beginRecording", "endRecording",
        "sendEvent", "flushEvents", "pendingEvents", "eventErrors", "eciErrors",
        "sessionSummary", "setStrictECI",
        "resync", "configureAutoDrift", "sampleDriftIfDue", "sampleDrift",
        "waitForDrift", "wait_for_drift", "driftEstimate", "driftSettings",
        "clockState", "getTime", "timeAtMonotonic",
    ):
        assert callable(getattr(EGINetStation, name, None)), name
