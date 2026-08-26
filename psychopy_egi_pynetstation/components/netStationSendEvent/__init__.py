from pathlib import Path

from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals
from psychopy.experiment.utils import CodeGenerationException

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent


class EGISendEventComponent(NetStationCommandComponent):
    """
    Sends a single event marker to a NetStation amplifier when this Component starts.

    With "Sync to screen refresh" enabled (the default), the marker is sent from a
    `win.callOnFlip()` callback, so its timestamp corresponds to the flip which
    actually put the stimulus on screen rather than the frame the code ran on.
    Upstream event sending is asynchronous by default, so this does not block the
    flip. "Target visual Component" can bind the marker to a named visual
    Component's first drawing flip; the marker must follow that target in Routine
    order.

    Requires an EGI Connect Component, with the same "Device label", placed
    earlier in the experiment.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationSendEvent.png"
    tooltip = "EGI Send Event: send an event marker to a NetStation amplifier"
    version = "0.1.0"
    beta = False
    commandMayBlock = False

    def __init__(
        self, exp, parentName,
        # basic
        name='egiSendEvent',
        startType='time (s)', startVal=0.0,
        stopType='duration (s)', stopVal='',
        startEstim='', durationEstim='',
        # device
        deviceLabel="netstation",
        # event
        targetComponent="",
        eventType="stim",
        eventLabel="",
        eventDesc="",
        eventData="",
        eventDuration=0.1,
        # data
        syncScreenRefresh=True,
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
        self.type = "EGISendEvent"

        # --- Event params ---
        self.order += [
            "targetComponent",
            "eventType",
            "eventLabel",
            "eventDesc",
            "eventData",
            "eventDuration",
        ]
        self.params['targetComponent'] = Param(
            targetComponent, valType="code", inputType="choice", categ="Basic",
            allowedVals=self.getTargetComponentVals,
            allowedLabels=self.getTargetComponentLabels,
            label="Target visual Component",
            hint=(
                "Optionally bind this marker to the first drawing flip of a visual "
                "Component in the same Routine. The EGI Send Event Component must "
                "be below the target in the Routine. Leave blank to use the normal "
                "Start settings."
            ),
        )
        self.params['eventType'] = Param(
            eventType, valType="str", inputType="single", categ="Basic",
            label="Event type",
            hint=(
                "Exactly 4 characters identifying this event, e.g. 'stim' or 'resp'. "
                "This is the main identifier NetStation uses, so pick something "
                "meaningful and document your event types."
            )
        )
        self.params['eventLabel'] = Param(
            eventLabel, valType="str", inputType="single", categ="Basic",
            label="Event label",
            hint=(
                "Up to 256 characters describing the event. Defaults to Event type "
                "if left blank."
            )
        )
        self.params['eventDesc'] = Param(
            eventDesc, valType="str", inputType="single", categ="Basic",
            label="Event description",
            hint="Up to 256 characters with further description of the event."
        )
        self.params['eventData'] = Param(
            eventData, valType="code", inputType="single", categ="Data",
            label="Event data",
            hint=(
                "Extra key/value data to attach to the event, as a Python dict, e.g. "
                "{'trl_': trialN, 'corr': True}. Keys must be exactly 4 characters; "
                "values must be str, bool, int or float."
            )
        )
        self.params['eventDuration'] = Param(
            eventDuration, valType="num", inputType="single", categ="Basic",
            label="Event duration (s)",
            hint=(
                "Duration recorded for the NetStation event in seconds. "
                "Defaults to 0.1; the minimum accepted value is 0.001."
            )
        )

        # --- Data params ---
        # BaseComponent already creates syncScreenRefresh, but doesn't surface it in
        # the dialog - redeclare it so users can see and change it.
        self.order += [
            "syncScreenRefresh",
        ]
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType="bool", inputType="bool", categ="Data",
            label="Sync to screen refresh",
            hint=(
                "Strongly recommended for markers tied to a visual stimulus. Sends "
                "the marker from a screen-flip callback, so it is timestamped to the "
                "flip which actually showed the stimulus. Target-bound markers are "
                "always flip synchronized, regardless of this setting."
            )
        )

        # A target-bound event gets its timing from the target's STARTED transition
        # and is necessarily flip synchronized. Start is a combined Builder control;
        # disabling that group prevents contradictory target and start schedules.
        self.depends.append({
            "dependsOn": "targetComponent",
            "condition": "!= ''",
            "param": "start",
            "true": "disable",
            "false": "enable",
        })

    def _routineComponents(self):
        """Components in this marker's Routine, or an empty list while loading."""
        routine = getattr(self.exp, "routines", {}).get(self.parentName)
        return list(routine) if routine is not None else []

    def _visualComponents(self):
        """Visual Components which can be selected as marker targets."""
        return [
            component
            for component in self._routineComponents()
            if (
                component is not self
                and isinstance(component, BaseVisualComponent)
                and not bool(component.params.get("disabled"))
            )
        ]

    def getTargetComponentVals(self):
        """Values for the target selector in Builder."""
        return [""] + [
            str(component.params["name"].val)
            for component in self._visualComponents()
        ]

    def getTargetComponentLabels(self):
        """Human-readable labels for the target selector in Builder."""
        return ["Use this marker's Start settings"] + [
            f"{component.params['name'].val} ({component.getShortType()})"
            for component in self._visualComponents()
        ]

    def _targetName(self):
        value = self.params["targetComponent"].val
        return str(value).strip() if value not in (None, "None") else ""

    def _targetComponent(self):
        targetName = self._targetName()
        if not targetName:
            return None
        for component in self._routineComponents():
            if str(component.params.get("name", "")) == targetName:
                return component
        return None

    def _validatedTargetComponent(self):
        """Resolve the configured target and reject unsafe generated ordering."""
        targetName = self._targetName()
        if not targetName:
            return None

        target = self._targetComponent()
        if target is None:
            raise CodeGenerationException(
                f"EGI Send Event target {targetName!r} does not exist in Routine "
                f"{self.parentName!r}. Select another Target visual Component."
            )
        if not isinstance(target, BaseVisualComponent):
            raise CodeGenerationException(
                f"EGI Send Event target {targetName!r} is not a visual Component."
            )
        if target.params.get("disabled"):
            raise CodeGenerationException(
                f"EGI Send Event target {targetName!r} is disabled."
            )

        components = self._routineComponents()
        if components.index(target) > components.index(self):
            raise CodeGenerationException(
                f"EGI Send Event must be below its target {targetName!r} in "
                f"Routine {self.parentName!r}; otherwise the marker would be one "
                "screen refresh late."
            )
        return target

    def _writeSendCode(self, buff, syncScreenRefresh):
        """Write the event call, optionally queued on the next window flip."""
        inits = getInitVals(self.params)
        # arguments are identical either way, so build them once
        args = (
            "    eventType=%(eventType)s,\n"
            "    duration=%(eventDuration)s,\n"
            "    label=%(eventLabel)s or %(eventType)s,\n"
            "    desc=%(eventDesc)s or '',\n"
            "    data=%(eventData)s or {},\n"
        )
        if syncScreenRefresh:
            # timestamp on the flip which actually shows the stimulus
            code = (
                "win.callOnFlip(\n"
                "    %(name)s.sendEvent,\n"
                + args +
                ")\n"
            )
        else:
            code = (
                "%(name)s.sendEvent(\n"
                "    start='now',\n"
                + args +
                ")\n"
            )
        buff.writeIndentedLines(code % inits)

    def writeCommandCode(self, buff):
        self._writeSendCode(buff, bool(self.params['syncScreenRefresh']))

    def writeFrameCode(self, buff):
        target = self._validatedTargetComponent()
        if target is None:
            return super().writeFrameCode(buff)

        params = self.params
        targetName = str(target.params["name"].val)
        buff.writeIndentedLines("\n# *%(name)s* target-bound updates\n" % params)
        code = (
            f"# queue this marker on the first flip which draws {targetName}\n"
            f"if %(name)s.status == NOT_STARTED and {targetName}.status == STARTED:\n"
            "    %(name)s.frameNStart = frameN\n"
            "    %(name)s.tStart = t\n"
            "    %(name)s.tStartRefresh = tThisFlipGlobal\n"
            "    win.timeOnFlip(%(name)s, 'tStartRefresh')\n"
        )
        if self.params['saveStartStop']:
            code += "    thisExp.timestampOnFlip(win, '%(name)s.started')\n"
        code += "    %(name)s.status = STARTED\n"
        buff.writeIndentedLines(code % params)
        buff.setIndentLevel(1, relative=True)
        self._writeSendCode(buff, syncScreenRefresh=True)
        buff.setIndentLevel(-1, relative=True)

EgiSendEventComponent = EGISendEventComponent
NetStationSendEventComponent = EGISendEventComponent
