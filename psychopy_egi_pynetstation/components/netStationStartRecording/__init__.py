from pathlib import Path

from psychopy.experiment.components import Param, getInitVals

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
        # drift
        waitForDrift=False,
        driftWaitTimeout=300.0,
        driftWaitPoll=1.0,
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
        self.exp.requirePsychopyLibs(['logging'])
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


EgiStartRecordingComponent = EGIStartRecordingComponent
NetStationStartRecordingComponent = EGIStartRecordingComponent
