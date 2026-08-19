from pathlib import Path

from psychopy.experiment.components import BaseComponent, Param, getInitVals

from psychopy_egi_pynetstation.components._base import addNetStationDeviceLabel


DEFAULT_NETSTATION_IP = "10.10.10.42"
DEFAULT_AMP_IP = "10.10.10.51"
DEFAULT_PORT = 55513


class NetStationInitComponent(BaseComponent):
    """
    Creates an EGI/Magstim NetStation network client, registering it internally so
    other NetStation Components (Connect, Disconnect, Start/Stop Recording, Send
    Event) can use it.

    Add exactly one of these per amplifier you want to use in your experiment, placed
    before any other NetStation Component. Other NetStation Components find this
    amplifier by looking for a device with the same "Device label" as this Component.

    This Component only registers the device - it does not open the connection. Follow it
    with an EGI Connect Component to actually connect.
    """
    plugin = "psychopy-egi-pynetstation"
    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / "netStationInit.png"
    tooltip = "NetStation Init: register a NetStation amplifier for use in this experiment"
    version = "0.1.0"
    beta = False

    def __init__(
        self, exp, parentName,
        # basic
        name='netStationInit',
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
        BaseComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            disabled=disabled,
        )
        addNetStationDeviceLabel(self, deviceLabel)
        self.type = "NetStationInit"
        self.url = "https://github.com/pmolfese/psychopy-egi-pynetstation"

        # writeExperimentEndCode reports failed event sends via logging
        self.exp.requirePsychopyLibs(['logging'])
        # Display-timing helpers. Requested unconditionally: the import block is
        # written before this Component's init code, and toggling the param in
        # Builder does not re-run __init__, so a conditional request would leave
        # a script that turns measurement on but never imports the module.
        self.exp.requireImport(
            importName="timing",
            importFrom="psychopy_egi_pynetstation",
            importAs="_nsTiming",
        )

        # --- Device params ---
        self.order += [
            "ip",
            "port",
            "ntpIP",
            "endian",
        ]
        self.params['ip'] = Param(
            ip, valType="str", inputType="single", categ="Device",
            label="NetStation IP address",
            hint=(
                "IP address of the NetStation host computer running the ECI server."
            )
        )
        self.params['port'] = Param(
            port, valType="int", inputType="single", categ="Device",
            label="Port",
            hint="Port the NetStation ECI server is listening on (usually 55513)."
        )
        self.params['ntpIP'] = Param(
            ntpIP, valType="str", inputType="single", categ="Device",
            label="Amplifier NTP IP address",
            hint=(
                "IP address of the NTP server on the amplifier, used to synchronize "
                "clocks. Leave blank to use the same address as 'NetStation IP "
                "address'. Default is 10.10.10.51."
            )
        )
        self.params['endian'] = Param(
            endian, valType="str", inputType="choice", categ="Device",
            allowedVals=["NTEL", "MAC-", "UNIX"],
            allowedLabels=[
                "NTEL - little-endian: modern Macs, Windows, most ARM64 Linux",
                "MAC- - big-endian: legacy PowerPC Macs",
                "UNIX - big-endian: legacy Unix, not most modern Linux",
            ],
            label="Endianness",
            hint=(
                "ECI byte-order option for the computer running PsychoPy, not the "
                "amplifier.\n\n"
                "NTEL: little-endian. Use for modern Intel Macs, Apple Silicon "
                "Macs, Windows x86/x64, and most ARM64 Linux.\n\n"
                "MAC-: big-endian. Use for legacy PowerPC-era Macs.\n\n"
                "UNIX: big-endian. Use only for legacy big-endian Unix systems; "
                "this option name is misleading for most modern Unix/Linux."
            ),
        )

        # --- Drift params ---
        self.order += [
            "driftMode",
            "driftInterval",
        ]
        self.params['driftMode'] = Param(
            driftMode, valType="str", inputType="choice", categ="Drift",
            allowedVals=["background", "off"],
            allowedLabels=[
                "Background thread",
                "Off",
            ],
            label="Drift correction",
            hint=(
                "Corrects event timestamps for clock drift between this computer and "
                "the amplifier. Background sampling is the default upstream behavior "
                "and needs no extra Builder Components."
            )
        )
        self.params['driftInterval'] = Param(
            driftInterval, valType="num", inputType="single", categ="Drift",
            label="Background sample interval (s)",
            hint="Target seconds between background drift samples."
        )
        # interval is meaningless with drift off
        self.depends.append({
            "dependsOn": "driftMode",
            "condition": "== 'off'",
            "param": "driftInterval",
            "true": "disable",
            "false": "enable",
        })

        # --- Display params ---
        self.order += [
            "measureRefresh",
            "warnSchedule",
        ]
        self.params['measureRefresh'] = Param(
            measureRefresh, valType="bool", inputType="bool", categ="Display",
            label="Measure display refresh at startup",
            hint=(
                "Measure the real refresh rate once at startup and record it "
                "alongside the recording. Takes 1-2 s and drops frames, but runs "
                "only at setup, never during trials.\n\n"
                "This changes no timing. Its value is diagnostic: a display running "
                "at, say, 60.0004 Hz instead of exactly 60 can put a one-frame step "
                "into stimulus presentation, and without the measured rate that is "
                "indistinguishable after the fact from a marker-timing bug."
            )
        )
        self.params['warnSchedule'] = Param(
            warnSchedule, valType="bool", inputType="bool", categ="Display",
            label="Warn about vulnerable schedules",
            hint=(
                "Compare your Routine durations against the measured refresh and "
                "warn once at startup if a duration is not a whole number of "
                "frames. Only checks Routines whose length is fully determined by "
                "fixed times in seconds - response-terminated or variable Routines "
                "have no fixed interval to beat against, and are skipped."
            )
        )
        self.depends.append({
            "dependsOn": "measureRefresh",
            "condition": "== True",
            "param": "warnSchedule",
            "true": "enable",
            "false": "disable",
        })

        # --- Debug params ---
        self.order += [
            "debug",
            "errorLog",
        ]
        self.params['debug'] = Param(
            debug, valType="bool", inputType="bool", categ="Data",
            label="Debug ECI traffic",
            hint="Print every ECI command and response byte to the console."
        )
        self.params['errorLog'] = Param(
            errorLog, valType="str", inputType="single", categ="Data",
            label="ECI error log file",
            hint=(
                "Optional path to write a JSON-lines log of ECI errors to. Leave "
                "blank for no log file."
            )
        )

    # --- display timing ---

    @staticmethod
    def _literalSeconds(param):
        """
        Value of a timing param as a plain number of seconds, or None if it
        isn't statically knowable (a variable, an expression, or blank).
        """
        val = getattr(param, "val", param)
        if isinstance(val, bool):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        text = str(val).strip()
        if not text or text.startswith("$"):
            return None
        try:
            return float(text)
        except ValueError:
            return None

    @classmethod
    def _componentEnd(cls, comp):
        """
        When a Component stops, in seconds from Routine start, or None if that
        can't be determined statically (frame units, conditions, variables).
        """
        params = getattr(comp, "params", {})
        stopType = str(getattr(params.get("stopType"), "val", "") or "")
        start = cls._literalSeconds(params.get("startVal"))
        stop = cls._literalSeconds(params.get("stopVal"))

        if stopType == "time (s)":
            return stop
        if stopType == "duration (s)":
            if start is None or stop is None:
                return None
            return start + stop
        # frame units, conditions, or anything blank: not statically knowable
        return None

    @classmethod
    def _routineDuration(cls, routine):
        """
        How long a Routine lasts, or None when that isn't fixed.

        Deliberately strict: if any Component's end time can't be resolved,
        the whole Routine is skipped. A Routine ended by a keypress has no
        fixed interval, so there is nothing for a beat to build up against -
        skipping it is correct, not a limitation.
        """
        ends = []
        for comp in routine:
            # our own command Components are momentary and never set the length
            if str(getattr(comp, "type", "")).startswith(("NetStation", "EGI")):
                continue
            # Routine settings carry no timing of their own
            if str(getattr(comp, "type", "")) == "RoutineSettings":
                continue
            end = cls._componentEnd(comp)
            if end is None:
                return None
            ends.append(end)
        if not ends:
            return None
        return max(ends)

    def _harvestSchedule(self):
        """
        Collect {duration_seconds: approximate trial count} across the flow.

        Durations are weighted by how many times each Routine actually runs,
        because the beat that matters is the one most trials use. Reporting
        the worst-rounding interval instead badly overstates the risk when one
        interval dominates the design.
        """
        weights = {}
        repeats = 1
        for entry in self.exp.flow:
            # loop initiators/terminators multiply how often Routines inside run
            loop = getattr(entry, "loop", None)
            if loop is not None:
                nReps = self._literalSeconds(
                    getattr(loop, "params", {}).get("nReps")
                )
                conditions = getattr(
                    getattr(loop, "params", {}).get("conditions"), "val", None
                )
                nConditions = len(conditions) if isinstance(conditions, list) else 1
                factor = int(nReps) if nReps else 1
                factor = max(1, factor) * max(1, nConditions)
                if type(entry).__name__.endswith("Initiator"):
                    repeats *= factor
                else:
                    repeats = max(1, repeats // factor)
                continue

            if not hasattr(entry, "__iter__"):
                continue
            duration = self._routineDuration(entry)
            if duration is None or duration <= 0:
                continue
            weights[duration] = weights.get(duration, 0) + repeats

        return weights

    # --- build-time checks ---

    # --- code generation ---

    def writeInitCode(self, buff):
        """
        Register this Component's NetStation device with DeviceManager, if a device with
        this Device label hasn't been registered already.
        """
        inits = getInitVals(self.params)
        # translate the drift mode into the two flags the device takes
        mode = str(self.params['driftMode'])
        inits['autoDrift'] = mode != "'off'"
        inits['autoDriftBackground'] = mode != "'off'"

        code = (
            "if deviceManager.getDevice(%(deviceLabel)s) is None:\n"
            "    # initialise EGI NetStation device for %(name)s\n"
            "    deviceManager.addDevice(\n"
            "        deviceClass='psychopy_egi_pynetstation.hardware.netstation.EGINetStation',\n"
            "        deviceName=%(deviceLabel)s,\n"
            "        ip=%(ip)s,\n"
            "        port=%(port)s,\n"
            "        ntpIP=%(ntpIP)s or None,\n"
            "        endian=%(endian)s,\n"
            "        driftCorrection=%(autoDrift)s,\n"
            "        autoDrift=%(autoDrift)s,\n"
            "        autoDriftInterval=%(driftInterval)s,\n"
            "        autoDriftBackground=%(autoDriftBackground)s,\n"
            "        debug=%(debug)s,\n"
            "        errorLog=%(errorLog)s or None,\n"
            "    )\n"
        )
        buff.writeIndentedLines(code % inits)

        self.writeDisplayTimingCode(buff, inits)

    def writeDisplayTimingCode(self, buff, inits):
        """
        Measure the display refresh once at setup, record it, and - if the
        schedule is statically knowable - warn when it is vulnerable to the
        frame beat.

        Measurement is setup-only: it takes 1-2 s and drops frames, so it must
        never run anywhere timing-critical.
        """
        if not self.params['measureRefresh']:
            return

        code = (
            "\n"
            "# measure the real display refresh (setup only - takes 1-2 s and\n"
            "# drops frames). Diagnostic: this changes no timing.\n"
            "_%(name)sFps, _%(name)sPeriod, _%(name)sSource = (\n"
            "    _nsTiming.measureDisplay(win)\n"
            ")\n"
            "logging.info(\n"
            "    f'NetStation display timing: {_%(name)sFps:.4f} Hz, '\n"
            "    f'{_%(name)sPeriod * 1000:.4f} ms/frame (%(name)s: '\n"
            "    f'{_%(name)sSource})'\n"
            ")\n"
            "if _%(name)sSource == 'assumed':\n"
            "    logging.warning(\n"
            "        'NetStation could not measure or read the display refresh '\n"
            "        'and is assuming 60 Hz. The frame beat is invisible at '\n"
            "        'exactly 60 Hz, so any schedule check below is unreliable.'\n"
            "    )\n"
        )
        buff.writeIndentedLines(code % inits)

        # record it alongside the recording, so a one-frame step is explicable
        # after the fact instead of looking like a marker-timing bug
        code = (
            "_%(name)sDev = deviceManager.getDevice(%(deviceLabel)s)\n"
            "if _%(name)sDev is not None:\n"
            "    _%(name)sDev.logDisplayTiming(\n"
            "        _%(name)sFps, _%(name)sPeriod, _%(name)sSource,\n"
            "        timing_mode='clock',\n"
            "    )\n"
        )
        buff.writeIndentedLines(code % inits)

        if not self.params['warnSchedule']:
            return

        # Durations are harvested at build time, weighted by how often each
        # Routine runs; the beat is reported for the interval most trials use.
        schedule = self._harvestSchedule()
        if not schedule:
            return

        inits = dict(inits)
        inits['scheduleLiteral'] = repr(
            {round(k, 9): int(v) for k, v in schedule.items()}
        )
        code = (
            "# Routine durations harvested from this experiment, weighted by\n"
            "# how many times each Routine runs.\n"
            "for _%(name)sMsg in _nsTiming.describeSchedule(\n"
            "    %(scheduleLiteral)s, _%(name)sPeriod\n"
            ")['messages']:\n"
            "    logging.warning(f'NetStation display timing: {_%(name)sMsg}')\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeExperimentEndCode(self, buff):
        """
        Event sends are asynchronous and can't raise into experiment code, so surface
        any failures at the end of the run rather than letting them vanish.
        """
        inits = getInitVals(self.params)
        code = (
            "# report any NetStation events which failed to send\n"
            "_%(name)sDevice = deviceManager.getDevice(%(deviceLabel)s)\n"
            "if _%(name)sDevice is not None:\n"
            "    _%(name)sErrors = _%(name)sDevice.eventErrors()\n"
            "    if _%(name)sErrors:\n"
            "        logging.error(\n"
            "            f'{len(_%(name)sErrors)} NetStation events failed to send: '\n"
            "            f'{_%(name)sErrors[:3]}'\n"
            "        )\n"
        )
        buff.writeIndentedLines(code % inits)
