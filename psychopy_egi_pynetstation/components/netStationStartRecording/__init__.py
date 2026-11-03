from pathlib import Path

from psychopy.experiment.components import Param, getInitVals

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent
from psychopy_egi_pynetstation.components._device import (
    EGINetStationDeviceBackend,
)
from psychopy_egi_pynetstation.components._display import (
    NetStationDisplayTimingMixin,
    addDisplayTimingParams,
)


class EgiStartRecordingComponent(
    NetStationDisplayTimingMixin, NetStationCommandComponent
):
    """
    Starts EEG recording on a NetStation amplifier when this Component starts.

    Requires an EGI NetStation device configured in Device Manager.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationStartRecording.png"
    iconSVG = Path(__file__).parent / "light" / "netStationStartRecording.svg"
    tooltip = "EGI Start Recording: start EEG recording on a NetStation amplifier"
    version = "0.1.1"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiStartRecording',
        startType='time (s)', startVal=0.0,
        stopType='duration (s)', stopVal='',
        startEstim='', durationEstim='',
        # device
        deviceLabel="",
        # drift
        waitForDrift=False,
        driftWaitTimeout=300.0,
        driftWaitPoll=1.0,
        # display
        measureRefresh=True,
        warnSchedule=True,
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
        self.type = "EgiStartRecording"
        self.exp.requirePsychopyLibs(['logging'])
        addDisplayTimingParams(
            self,
            measureRefresh=measureRefresh,
            warnSchedule=warnSchedule,
        )
        self.order += [
            "waitForDrift",
            "driftWaitTimeout",
            "driftWaitPoll",
        ]
        self.params['waitForDrift'] = Param(
            waitForDrift, valType="bool", inputType="bool", categ="Drift",
            label="Wait until drift correction is ready",
            hint=(
                "After starting recording, block until the upstream drift model "
                "reports it is ready. Use this during setup or a deliberate "
                "pre-run pause before timing-critical events."
            ),
        )
        self.params['driftWaitTimeout'] = Param(
            driftWaitTimeout, valType="num", inputType="single", categ="Drift",
            label="Drift wait timeout (s)",
            hint="Maximum seconds to wait for drift correction to become ready.",
        )
        self.params['driftWaitPoll'] = Param(
            driftWaitPoll, valType="num", inputType="single", categ="Drift",
            label="Drift wait poll interval (s)",
            hint="Seconds between drift-readiness checks while waiting.",
        )
        for name in ("driftWaitTimeout", "driftWaitPoll"):
            self.depends.append({
                "dependsOn": "waitForDrift",
                "condition": "== True",
                "param": name,
                "true": "enable",
                "false": "disable",
            })

    def writeInitCode(self, buff):
        NetStationCommandComponent.writeInitCode(self, buff)
        self.writeDisplayTimingCode(buff)

    def writeCommandCode(self, buff):
        inits = getInitVals(self.params)
        code = "%(name)s.beginRecording()\n"
        if self.params['waitForDrift']:
            code += (
                "logging.info(\n"
                "    \"Waiting for NetStation drift correction to become ready.\"\n"
                ")\n"
                "%(name)s.waitForDrift(\n"
                "    timeout=%(driftWaitTimeout)s,\n"
                "    poll=%(driftWaitPoll)s,\n"
                ")\n"
            )
        buff.writeIndentedLines(code % inits)


NetStationStartRecordingComponent = EgiStartRecordingComponent

EgiStartRecordingComponent.registerBackend(EGINetStationDeviceBackend)
