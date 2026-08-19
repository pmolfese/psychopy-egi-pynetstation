import re

from psychopy.experiment.components import BaseComponent, Param, getInitVals


class NetStationDeviceLabelParam(Param):
    """Text label which cannot be restored as a Device Manager selector."""

    @property
    def valType(self):
        return "str"

    @valType.setter
    def valType(self, value):
        # PsychoPy restores valType from saved .psyexp XML. Older versions of
        # this plugin saved "device" here, which would make PsychoPy demand a
        # Device Manager configuration. Always migrate that metadata to text.
        pass


def addNetStationDeviceLabel(component, deviceLabel="netstation"):
    """Add the internal registry label shared by all NetStation Components."""
    # Configuration lives in EGI Connect. DeviceManager is only the runtime
    # registry through which the other EGI Components retrieve that client.
    component.exp.requirePsychopyLibs(['hardware'])
    component.exp.requireImport(
        importName="NetStationComponentState",
        importFrom="psychopy_egi_pynetstation.component_state",
        importAs="_NetStationComponentState",
    )
    component.order += ["deviceLabel"]
    component.params['deviceLabel'] = NetStationDeviceLabelParam(
        deviceLabel,
        valType="str",
        inputType="single",
        categ="Device",
        label="Device label",
        hint=(
            "Internal name used to share this NetStation connection between EGI "
            "Components. This is not a Device Manager selection. Keep the default "
            "unless the experiment uses more than one NetStation connection."
        ),
    )


def normalizeNetStationStartValue(component):
    """Rewrite invalid leading-zero decimal integers before code generation."""
    param = component.params.get('startVal')
    value = getattr(param, 'val', None)
    if not isinstance(value, str):
        return

    text = value.strip()
    if re.fullmatch(r"[+-]?0[0-9]+", text):
        # Python 3 rejects literals such as 04. Builder users still mean the
        # decimal value 4, so make that interpretation explicit while leaving
        # expressions and variables untouched.
        param.val = str(int(text, 10))


def writeNetStationTimingRefresh(buff):
    """Refresh Builder's frame clocks after a blocking network command."""
    code = (
        "# refresh Routine clocks after the blocking NetStation command\n"
        "t = routineTimer.getTime()\n"
        "tThisFlip = win.getFutureFlipTime(clock=routineTimer)\n"
        "tThisFlipGlobal = win.getFutureFlipTime(clock=None)\n"
    )
    buff.writeIndentedLines(code)


class NetStationCommandComponent(BaseComponent):
    """
    Base class for NetStation Components which send a single one-off command (e.g.
    connect, disconnect, start recording) to an already-registered NetStation device.

    Subclasses must set `type` and override `writeCommandCode` to write the line(s) of
    code which send their particular command. The command fires once, when the
    Component starts - its stop time/duration is not used.
    """
    commandMayBlock = True

    def __init__(
        self, exp, parentName,
        name='',
        startType='time (s)', startVal=0.0,
        stopType='duration (s)', stopVal='',
        startEstim='', durationEstim='',
        deviceLabel="netstation",
        disabled=False,
    ):
        BaseComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            disabled=disabled,
        )
        addNetStationDeviceLabel(self, deviceLabel)
        self.url = "https://github.com/pmolfese/psychopy-egi-pynetstation"

    def writeInitCode(self, buff):
        """
        Wrap the registered device in lifecycle state private to this Component.

        The hardware connection is shared, but PsychoPy's ``status`` and timing
        attributes must not be: multiple NetStation Components can coexist in one
        Routine and start independently.
        """
        inits = getInitVals(self.params)
        code = (
            "_%(name)sDevice = deviceManager.getDevice(%(deviceLabel)s)\n"
            "if _%(name)sDevice is None:\n"
            "    raise ValueError(\n"
            "        \"No NetStation device found for Device label %(deviceLabel)s - be \"\n"
            "        \"sure to add an EGI Connect Component with the same \"\n"
            "        \"Device label, before this Component.\"\n"
            "    )\n"
            "%(name)s = _NetStationComponentState(\n"
            "    _%(name)sDevice, status=NOT_STARTED\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeCommandCode(self, buff):
        """
        Write the code which sends this Component's command. Called once, inside the
        "if this Component is starting this frame" block. Subclasses must override this.
        """
        raise NotImplementedError(
            "Subclasses of NetStationCommandComponent must implement writeCommandCode"
        )

    def writeFrameCode(self, buff):
        normalizeNetStationStartValue(self)
        params = self.params
        code = (
            "\n"
            "# *%(name)s* updates\n"
        )
        buff.writeIndentedLines(code % params)

        # commands are momentary - only ever fire once, when the Component starts
        indented = self.writeStartTestCode(buff)
        if indented:
            self.writeCommandCode(buff)
            if self.commandMayBlock:
                writeNetStationTimingRefresh(buff)
            buff.setIndentLevel(-indented, relative=True)
