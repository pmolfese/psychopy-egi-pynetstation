from pathlib import Path

from psychopy.experiment.components import Param, getInitVals

from psychopy_egi_pynetstation.components._base import NetStationCommandComponent


class EgiSendEventComponent(NetStationCommandComponent):
    """
    Sends a single event marker to a NetStation amplifier when this Component starts.

    With "Sync to screen refresh" enabled (the default), the marker is sent from a
    `win.callOnFlip()` callback, so its timestamp corresponds to the flip which
    actually put the stimulus on screen rather than the frame the code ran on.
    Upstream event sending is asynchronous by default, so this does not block the
    flip.

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
            "eventType",
            "eventLabel",
            "eventDesc",
            "eventData",
            "eventDuration",
        ]
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
                "flip which actually showed the stimulus."
            )
        )

    def writeCommandCode(self, buff):
        inits = getInitVals(self.params)
        # arguments are identical either way, so build them once
        args = (
            "    eventType=%(eventType)s,\n"
            "    duration=%(eventDuration)s,\n"
            "    label=%(eventLabel)s or %(eventType)s,\n"
            "    desc=%(eventDesc)s or '',\n"
            "    data=%(eventData)s or {},\n"
        )
        if self.params['syncScreenRefresh']:
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

EGISendEventComponent = EgiSendEventComponent
NetStationSendEventComponent = EgiSendEventComponent
