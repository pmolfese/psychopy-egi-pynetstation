from psychopy_egi_pynetstation.component_state import NetStationComponentState


class FakeNetStation:
    def __init__(self):
        self.commands = []

    def connect(self):
        self.commands.append("connect")

    def beginRecording(self):
        self.commands.append("beginRecording")

    def sendEvent(self, eventType):
        self.commands.append(("sendEvent", eventType))


def test_component_states_share_device_but_not_lifecycle_fields():
    device = FakeNetStation()
    connect = NetStationComponentState(device, status="NOT_STARTED")
    start = NetStationComponentState(device, status="NOT_STARTED")
    event = NetStationComponentState(device, status="NOT_STARTED")

    connect.status = "STARTED"
    connect.tStart = 0.0
    connect.connect()

    assert start.status == "NOT_STARTED"
    assert event.status == "NOT_STARTED"
    assert not hasattr(start, "tStart")

    start.status = "STARTED"
    start.beginRecording()
    event.status = "STARTED"
    event.sendEvent(eventType="stim")

    assert connect.device is start.device is event.device is device
    assert device.commands == ["connect", "beginRecording", ("sendEvent", "stim")]
