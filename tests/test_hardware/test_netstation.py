import pytest

# the device wrapper subclasses psychopy.hardware.base.BaseDevice
pytest.importorskip("psychopy.hardware.base")

from egi_pynetstation.exceptions import NetStationUnconnected  # noqa: E402

from psychopy_egi_pynetstation.hardware.netstation import EGINetStation  # noqa: E402


@pytest.fixture
def device():
    # constructing EGINetStation doesn't open a socket, so this is safe
    # without a real amplifier on the network
    return EGINetStation(ip="127.0.0.1", port=55513)


def test_construct_does_not_connect(device):
    assert device._connected is False
    assert device.ip == "127.0.0.1"
    assert device.port == 55513
    assert device.ntpIP == "10.10.10.51"


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


# --- egi-pynetstation 2.0.0 surface ---


def test_drift_defaults_are_background(device):
    # upstream now samples drift in the background by default
    assert device.driftCorrection is True
    assert device.autoDrift is True
    assert device.autoDriftBackground is True

    cooperative = EGINetStation(ip="127.0.0.1", autoDriftBackground=False)
    assert cooperative.autoDriftBackground is False


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
    assert device.pendingEvents() == 0


def test_drift_calls_require_connection(device):
    # both are @check_connected upstream
    with pytest.raises(NetStationUnconnected):
        device.configureAutoDrift(enabled=True, interval=30.0)

    with pytest.raises(NetStationUnconnected):
        device.sampleDriftIfDue(availablePause=1.0)


def test_wrapper_exposes_expected_api():
    # guard against silently losing a method the Builder Components call
    for name in (
        "connect", "disconnect",
        "beginRecording", "endRecording",
        "sendEvent", "flushEvents", "pendingEvents", "eventErrors",
        "resync", "configureAutoDrift", "sampleDriftIfDue", "sampleDrift",
        "driftEstimate", "clockState", "getTime", "timeAtMonotonic",
    ):
        assert callable(getattr(EGINetStation, name, None)), name
