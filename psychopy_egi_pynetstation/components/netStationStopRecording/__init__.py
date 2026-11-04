from pathlib import Path

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent
from psychopy_egi_pynetstation.components._device import (
    EGINetStationDeviceBackend,
)


class EgiStopRecordingComponent(NetStationCommandComponent):
    """
    Stops EEG recording on a NetStation amplifier when this Component starts.

    Requires an EGI NetStation device configured in Device Manager.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationStopRecording.png"
    iconSVG = Path(__file__).parent / "light" / "netStationStopRecording.svg"
    tooltip = "EGI Stop Recording: stop EEG recording on a NetStation amplifier"
    version = "0.1.2"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiStopRecording',
        startType='time (s)', startVal=0.0,
        stopType='duration (s)', stopVal='',
        startEstim='', durationEstim='',
        # device
        deviceLabel="",
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
        self.type = "EgiStopRecording"

    def writeCommandCode(self, buff):
        code = "%(name)s.endRecording()\n"
        buff.writeIndentedLines(code % self.params)


NetStationStopRecordingComponent = EgiStopRecordingComponent

EgiStopRecordingComponent.registerBackend(EGINetStationDeviceBackend)
