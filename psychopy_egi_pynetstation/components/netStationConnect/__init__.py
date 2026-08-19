from pathlib import Path

from psychopy.experiment.components import getInitVals

from psychopy_egi_pynetstation.components.netStationInit import (
    DEFAULT_AMP_IP,
    DEFAULT_NETSTATION_IP,
    DEFAULT_PORT,
    NetStationInitComponent,
)
from psychopy_egi_pynetstation.components._base import (
    normalizeNetStationStartValue,
    writeNetStationTimingRefresh,
)


class EgiConnectComponent(NetStationInitComponent):
    """
    Creates an EGI/Magstim NetStation client from the network settings in this
    Component, then opens the TCP/IP connection when the Component starts.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationConnect.png"
    tooltip = "EGI Connect: configure and connect to a NetStation amplifier over TCP/IP"
    version = "0.1.0"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiConnect',
        startType='time (s)', startVal=0.0,
        stopType='duration (s)', stopVal='',
        startEstim='', durationEstim='',
        # device
        deviceLabel="netstation",
        ip=DEFAULT_NETSTATION_IP,
        port=DEFAULT_PORT,
        ntpIP=DEFAULT_AMP_IP,
        endian="NTEL",
        # drift
        driftMode="background",
        driftInterval=15.0,
        # display
        measureRefresh=True,
        warnSchedule=True,
        # debug
        debug=False,
        errorLog="",
        # testing
        disabled=False,
    ):
        NetStationInitComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            deviceLabel=deviceLabel,
            ip=ip,
            port=port,
            ntpIP=ntpIP,
            endian=endian,
            driftMode=driftMode,
            driftInterval=driftInterval,
            measureRefresh=measureRefresh,
            warnSchedule=warnSchedule,
            debug=debug,
            errorLog=errorLog,
            disabled=disabled,
        )
        self.type = "EGIConnect"

    def writeInitCode(self, buff):
        """
        Register the device and give this Component independent lifecycle state.
        """
        NetStationInitComponent.writeInitCode(self, buff)
        inits = getInitVals(self.params)
        code = (
            "_%(name)sDevice = deviceManager.getDevice(%(deviceLabel)s)\n"
            "if _%(name)sDevice is None:\n"
            "    raise ValueError(\n"
            "        \"No NetStation device found for Device label %(deviceLabel)s.\"\n"
            "    )\n"
            "%(name)s = _NetStationComponentState(\n"
            "    _%(name)sDevice, status=NOT_STARTED\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeCommandCode(self, buff):
        code = "%(name)s.connect()\n"
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        normalizeNetStationStartValue(self)
        params = self.params
        code = (
            "\n"
            "# *%(name)s* updates\n"
        )
        buff.writeIndentedLines(code % params)

        # Connect is momentary - only fire once, when the Component starts.
        indented = self.writeStartTestCode(buff)
        if indented:
            self.writeCommandCode(buff)
            writeNetStationTimingRefresh(buff)
            buff.setIndentLevel(-indented, relative=True)


EGIConnectComponent = EgiConnectComponent
NetStationConnectComponent = EgiConnectComponent
