from pathlib import Path

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent


class EGIStopRecordingComponent(NetStationCommandComponent):
    """
    Stops EEG recording on a NetStation amplifier when this Component starts.

    Requires an EGI Connect Component, with the same "Device label", placed
    earlier in the experiment.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationStopRecording.png"
    tooltip = "EGI Stop Recording: stop EEG recording on a NetStation amplifier"
    version = "0.1.0"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiStopRecording',
        startType='time (s)', startVal=0.0,
        stopType='duration (s)', stopVal='',
        startEstim='', durationEstim='',
        # device
        deviceLabel="netstation",
        # testing
        disabled=False,
    ):
        NetStationCommandComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            deviceLabel=deviceLabel,
            disabled=disabled,
        )
        self.type = "EGIStopRecording"

    def writeCommandCode(self, buff):
        code = "%(name)s.endRecording()\n"
        buff.writeIndentedLines(code % self.params)


EgiStopRecordingComponent = EGIStopRecordingComponent
NetStationStopRecordingComponent = EGIStopRecordingComponent
