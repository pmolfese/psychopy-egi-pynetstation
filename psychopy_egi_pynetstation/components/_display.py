"""Builder helpers for startup display-timing diagnostics."""

from psychopy.experiment.components import Param, getInitVals


def addDisplayTimingParams(component, measureRefresh=True, warnSchedule=True):
    """Add session-level display diagnostic controls to a Component."""
    component.exp.requirePsychopyLibs(["logging"])
    component.exp.requireImport(
        importName="timing",
        importFrom="psychopy_egi_pynetstation",
        importAs="_nsTiming",
    )
    component.order += ["measureRefresh", "warnSchedule"]
    component.params["measureRefresh"] = Param(
        measureRefresh,
        valType="bool", inputType="bool", categ="Display",
        label="Measure display refresh at startup",
        hint=(
            "Measure the real refresh rate once during experiment setup and "
            "record it alongside the NetStation session."
        ),
    )
    component.params["warnSchedule"] = Param(
        warnSchedule,
        valType="bool", inputType="bool", categ="Display",
        label="Warn about vulnerable schedules",
        hint=(
            "Compare fixed Routine durations with the measured refresh rate "
            "and warn about schedules vulnerable to a one-frame beat."
        ),
    )
    component.depends.append({
        "dependsOn": "measureRefresh",
        "condition": "== True",
        "param": "warnSchedule",
        "true": "enable",
        "false": "disable",
    })


class NetStationDisplayTimingMixin:
    """Analyze fixed Routine durations and write startup measurement code."""

    @staticmethod
    def _literalSeconds(param):
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
        return None

    @classmethod
    def _routineDuration(cls, routine):
        ends = []
        for comp in routine:
            componentType = str(getattr(comp, "type", ""))
            if componentType.startswith(("NetStation", "EGI")):
                continue
            if componentType == "RoutineSettings":
                continue
            end = cls._componentEnd(comp)
            if end is None:
                return None
            ends.append(end)
        return max(ends) if ends else None

    def _harvestSchedule(self):
        weights = {}
        repeats = 1
        for entry in self.exp.flow:
            loop = getattr(entry, "loop", None)
            if loop is not None:
                nReps = self._literalSeconds(
                    getattr(loop, "params", {}).get("nReps")
                )
                conditions = getattr(
                    getattr(loop, "params", {}).get("conditions"), "val", None
                )
                nConditions = len(conditions) if isinstance(conditions, list) else 1
                factor = max(1, int(nReps) if nReps else 1)
                factor *= max(1, nConditions)
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

    def writeDisplayTimingCode(self, buff):
        """Measure refresh during setup and record/warn before trials begin."""
        if not self.params["measureRefresh"]:
            return
        inits = getInitVals(self.params)
        code = (
            "\n"
            "# measure display refresh during setup (never during trials)\n"
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
            "        'NetStation could not measure or read the display refresh; '\n"
            "        'assuming 60 Hz, so schedule warnings may be unreliable.'\n"
            "    )\n"
            "_%(name)sDevice.logDisplayTiming(\n"
            "    _%(name)sFps, _%(name)sPeriod, _%(name)sSource,\n"
            "    timing_mode='clock',\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

        if not self.params["warnSchedule"]:
            return
        schedule = self._harvestSchedule()
        if not schedule:
            return
        values = dict(inits)
        values["scheduleLiteral"] = repr(
            {round(k, 9): int(v) for k, v in schedule.items()}
        )
        code = (
            "# Routine durations harvested at build time and weighted by use.\n"
            "for _%(name)sMsg in _nsTiming.describeSchedule(\n"
            "    %(scheduleLiteral)s, _%(name)sPeriod\n"
            ")[\"messages\"]:\n"
            "    logging.warning(f'NetStation display timing: {_%(name)sMsg}')\n"
        )
        buff.writeIndentedLines(code % values)


__all__ = ["NetStationDisplayTimingMixin", "addDisplayTimingParams"]
