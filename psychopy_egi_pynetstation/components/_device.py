"""PsychoPy Studio DeviceManager backend for EGI NetStation."""

from psychopy.experiment.components import Param, getInitVals
from psychopy.experiment.devices import DeviceBackend

from ._startup import addStartupParams

from psychopy_egi_pynetstation.hardware.netstation import (
    DEFAULT_AMP_IP,
    DEFAULT_NETSTATION_IP,
    DEFAULT_PORT,
)


class EGINetStationDeviceBackend(DeviceBackend):
    """Editable DeviceManager profile for a networked NetStation host."""

    backendLabel = "EGI NetStation"
    deviceClass = (
        "psychopy_egi_pynetstation.hardware.netstation.EGINetStation"
    )
    plugin = "psychopy-egi-pynetstation"

    def __init__(self, profile):
        super().__init__(profile)
        self.depends = []
        self.order += [
            "dummyMode",
            "ip",
            "port",
            "ntpIP",
            "endian",
            "driftMode",
            "driftWarmup",
            "driftInterval",
            "debug",
            "errorLog",
            "strictECI",
        ]

        self.params["dummyMode"] = Param(
            profile.get("dummyMode", False), valType="bool", inputType="bool", categ="Device",
            label="Dummy mode — run without EEG hardware",
            hint="Run offline: no EEG is recorded and no markers are sent to hardware.",
        )
        addStartupParams(
            self, profile.get("chooseAtStartup", False), profile.get("askOnFailure", False)
        )
        self.params["ip"] = Param(
            profile.get("ip", DEFAULT_NETSTATION_IP),
            valType="str", inputType="single", categ="Device",
            label="NetStation IP address",
            hint="IP address of the NetStation host running the ECI server.",
        )
        self.params["port"] = Param(
            profile.get("port", DEFAULT_PORT),
            valType="int", inputType="single", categ="Device",
            label="Port",
            hint="Port on which the NetStation ECI server listens (usually 55513).",
        )
        self.params["ntpIP"] = Param(
            profile.get("ntpIP", DEFAULT_AMP_IP),
            valType="str", inputType="single", categ="Device",
            label="Amplifier NTP IP address",
            hint=(
                "IP address of the amplifier NTP server. Leave blank to use "
                "the NetStation host address."
            ),
        )
        self.params["endian"] = Param(
            profile.get("endian", "NTEL"),
            valType="str", inputType="choice", categ="Device",
            allowedVals=["NTEL", "MAC-", "UNIX"],
            allowedLabels=[
                "NTEL - little-endian: Intel/Apple Silicon Macs, Windows, "
                "most ARM64 Linux",
                "MAC- - big-endian: legacy PowerPC Macs",
                "UNIX - big-endian: legacy Unix, not most modern Linux",
            ],
            label="Endianness",
            hint=(
                "ECI byte order for the computer running PsychoPy. NTEL is "
                "correct for modern Intel and Apple Silicon Macs, Windows, "
                "and most ARM64 Linux systems. MAC- and UNIX are only for "
                "legacy big-endian systems."
            ),
        )
        self.params["driftMode"] = Param(
            "background",
            valType="str", inputType="choice", categ="Drift",
            allowedVals=["background", "off"],
            allowedLabels=["Background thread", "Off"],
            label="Drift correction",
            hint=(
                "Correct event timestamps for clock drift. Background "
                "sampling is automatic and is the recommended mode."
            ),
        )
        self.params["driftWarmup"] = Param(
            False,
            valType="bool", inputType="bool", categ="Drift",
            label="Enable drift warmup",
            hint=(
                "Build a provisional drift model before the ordinary model "
                "has collected enough samples."
            ),
        )
        self.params["driftInterval"] = Param(
            15.0,
            valType="num", inputType="single", categ="Drift",
            label="Background sample interval (s)",
            hint="Target seconds between background NTP drift samples.",
        )
        for name in ("driftWarmup", "driftInterval"):
            self.depends.append({
                "dependsOn": "driftMode",
                "condition": "== 'off'",
                "param": name,
                "true": "disable",
                "false": "enable",
            })

        self.params["debug"] = Param(
            False,
            valType="bool", inputType="bool", categ="Data",
            label="Debug ECI traffic",
            hint="Print every ECI command and response byte to the console.",
        )
        self.params["errorLog"] = Param(
            "",
            valType="str", inputType="single", categ="Data",
            label="ECI error log file",
            hint="Optional JSON-lines diagnostic log path.",
        )
        self.params["strictECI"] = Param(
            False,
            valType="bool", inputType="bool", categ="Data",
            label="Strict ECI responses",
            hint=(
                "Raise when a blocking ECI command receives a rejected or "
                "malformed response."
            ),
        )

    def writeDeviceCode(self, buff):
        """Create and connect the device during Studio device setup."""
        inits = getInitVals(self.params)
        mode = str(self.params["driftMode"])
        inits["autoDrift"] = mode != "'off'"
        inits["autoDriftBackground"] = mode != "'off'"
        inits["driftWarmupEnabled"] = (
            mode != "'off'" and bool(self.params["driftWarmup"])
        )
        inits["dummyExpression"] = "%(dummyMode)s" % inits
        if self.params["chooseAtStartup"]:
            inits["dummyExpression"] = (
                "_nsResolveMode(expInfo, %(name)s, dummyMode=%(dummyMode)s, chooseAtStartup=True)"
            ) % inits
        inits["failureCallback"] = "onFailure=_nsAskFailure" if self.params["askOnFailure"] else ""
        code = (
            "from psychopy_egi_pynetstation.startup import (\n"
            "    resolveDummyMode as _nsResolveMode, askConnectionFailure as _nsAskFailure,\n"
            ")\n"
            "# initialize and connect %(name)s\n"
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy_egi_pynetstation.hardware.netstation.EGINetStation',\n"
            "    deviceName=%(name)s,\n"
            "    dummyMode=%(dummyExpression)s,\n"
            "    ip=%(ip)s,\n"
            "    port=%(port)s,\n"
            "    ntpIP=%(ntpIP)s or None,\n"
            "    endian=%(endian)s,\n"
            "    driftCorrection=%(autoDrift)s,\n"
            "    autoDrift=%(autoDrift)s,\n"
            "    driftWarmup=%(driftWarmupEnabled)s,\n"
            "    autoDriftInterval=%(driftInterval)s,\n"
            "    autoDriftBackground=%(autoDriftBackground)s,\n"
            "    debug=%(debug)s,\n"
            "    errorLog=%(errorLog)s or None,\n"
            "    strictECI=%(strictECI)s,\n"
            ")\n"
            "deviceManager.getDevice(%(name)s).setRunInfo(expInfo, %(name)s)\n"
            "deviceManager.getDevice(%(name)s).connect(%(failureCallback)s)\n"
        )
        buff.writeIndentedLines(code % inits)


__all__ = ["EGINetStationDeviceBackend"]
