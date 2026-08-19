from pathlib import Path

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent


class EgiDisconnectComponent(NetStationCommandComponent):
    """
    Closes the TCP/IP connection to a NetStation amplifier when this Component starts.

    Requires an EGI Connect Component, with the same "Device label", placed
    earlier in the experiment.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationDisconnect.png"
    tooltip = "EGI Disconnect: close the connection to a NetStation amplifier"
    version = "0.1.0"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiDisconnect',
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
        self.type = "EGIDisconnect"

    def writeCommandCode(self, buff):
        code = "%(name)s.disconnect()\n"
        buff.writeIndentedLines(code % self.params)


EGIDisconnectComponent = EgiDisconnectComponent
NetStationDisconnectComponent = EgiDisconnectComponent
