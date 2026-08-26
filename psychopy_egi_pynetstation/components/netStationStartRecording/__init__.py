from pathlib import Path

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent


class EGIStartRecordingComponent(NetStationCommandComponent):
    """
    Starts EEG recording on a NetStation amplifier when this Component starts.

    Requires an EGI Connect Component, with the same "Device label", placed
    earlier in the experiment.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationStartRecording.png"
    tooltip = "EGI Start Recording: start EEG recording on a NetStation amplifier"
    version = "0.1.0"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiStartRecording',
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
        self.type = "EGIStartRecording"

    def writeCommandCode(self, buff):
        code = "%(name)s.beginRecording()\n"
        buff.writeIndentedLines(code % self.params)


EgiStartRecordingComponent = EGIStartRecordingComponent
NetStationStartRecordingComponent = EGIStartRecordingComponent
