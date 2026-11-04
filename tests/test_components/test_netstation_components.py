"""
Tests for the NetStation Builder Components. These require a full PsychoPy
install (the `tests` extra), so are skipped otherwise.
"""
import pytest
from importlib.metadata import entry_points

# these need the full Builder machinery, not just the psychopy namespace
_experiment = pytest.importorskip("psychopy.experiment")
Experiment = getattr(_experiment, "Experiment", None)
if Experiment is None:  # pragma: no cover - partial/stubbed install
    pytest.skip(
        "a full PsychoPy install is required for Component tests",
        allow_module_level=True,
    )

from psychopy_egi_pynetstation.components.netStationInit import (  # noqa: E402
    NetStationInitComponent,
)
from psychopy_egi_pynetstation.components._device import (  # noqa: E402
    EGINetStationDeviceBackend,
)
from psychopy_egi_pynetstation.components.netStationConnect import (  # noqa: E402
    EgiConnectComponent,
)
from psychopy_egi_pynetstation.components.netStationDisconnect import (  # noqa: E402
    EgiDisconnectComponent,
)
from psychopy_egi_pynetstation.components.netStationStartRecording import (  # noqa: E402
    EgiStartRecordingComponent,
)
from psychopy_egi_pynetstation.components.netStationStopRecording import (  # noqa: E402
    EgiStopRecordingComponent,
)
from psychopy_egi_pynetstation.components.netStationSendEvent import (  # noqa: E402
    EgiSendEventComponent,
)
from psychopy.experiment.components.text import TextComponent  # noqa: E402
from psychopy.experiment.exports import IndentingBuffer  # noqa: E402
from psychopy.experiment.utils import CodeGenerationException  # noqa: E402


@pytest.fixture
def routine():
    exp = Experiment()
    exp.addRoutine("trial")
    exp.flow.addRoutine(exp.routines["trial"], pos=0)
    return exp.routines["trial"]


def test_plugin_entry_points_include_active_and_legacy_components():
    names = {
        ep.name
        for ep in entry_points(group="psychopy.experiment.components")
        if ep.value.startswith("psychopy_egi_pynetstation.")
    }

    assert names == {
        "EgiConnectComponent",
        "EgiStartRecordingComponent",
        "EgiStopRecordingComponent",
        "EgiDisconnectComponent",
        "EgiSendEventComponent",
    }

    assert not EgiStartRecordingComponent.hidden
    assert not EgiStopRecordingComponent.hidden
    assert not EgiSendEventComponent.hidden
    assert EgiConnectComponent.hidden
    assert EgiDisconnectComponent.hidden


def test_builder_component_names_use_studio_compatible_egi_prefix():
    import re

    expected = {
        EgiConnectComponent: "Egi Connect",
        EgiStartRecordingComponent: "Egi Start Recording",
        EgiStopRecordingComponent: "Egi Stop Recording",
        EgiDisconnectComponent: "Egi Disconnect",
        EgiSendEventComponent: "Egi Send Event",
    }
    for component_class, expected_label in expected.items():
        # Mirrors ComponentButton.svelte's current titleCase implementation.
        label = component_class.__name__.replace("Component", "")
        label = re.sub(r"(\w)([A-Z])", r"\1 \2", label)
        assert label == expected_label


def test_uppercase_component_class_names_are_not_exported():
    modules = (
        "netStationConnect",
        "netStationStartRecording",
        "netStationStopRecording",
        "netStationDisconnect",
        "netStationSendEvent",
    )
    for module_name in modules:
        module = __import__(
            f"psychopy_egi_pynetstation.components.{module_name}",
            fromlist=["*"],
        )
        assert not any(
            name.startswith("EGI") and name.endswith("Component")
            for name in vars(module)
        )


def test_all_entrypoint_component_templates_serialize():
    for componentClass in (
        EgiConnectComponent,
        EgiStartRecordingComponent,
        EgiStopRecordingComponent,
        EgiDisconnectComponent,
        EgiSendEventComponent,
    ):
        template = componentClass.getTemplateJSON()
        assert template["__name__"] == componentClass.__name__


@pytest.mark.parametrize("componentClass", [
    EgiStartRecordingComponent,
    EgiStopRecordingComponent,
    EgiSendEventComponent,
])
def test_visible_components_include_studio_svg_icons(componentClass):
    assert componentClass.iconSVG.suffix == ".svg"
    assert componentClass.iconSVG.is_file()
    assert "<svg" in componentClass.getTemplateJSON()["iconSVG"]


@pytest.mark.parametrize("componentClass", [
    EgiStartRecordingComponent,
    EgiStopRecordingComponent,
    EgiSendEventComponent,
])
def test_active_components_use_device_manager_selector(routine, componentClass):
    comp = componentClass(routine.exp, routine.name, deviceLabel="netstation")

    label = comp.params["deviceLabel"]
    assert label.val == "netstation"
    assert label.valType == "device"
    assert label.inputType == "device"
    assert EGINetStationDeviceBackend in label.allowedVals


def test_device_backend_template_and_generated_code():
    profile = {
        "deviceName": "EGI NetStation (manual configuration)",
        "ip": "10.0.0.42",
        "port": 55513,
        "ntpIP": "10.0.0.51",
        "endian": "NTEL",
    }
    backend = EGINetStationDeviceBackend(profile)
    backend.params["name"].val = "netstation"
    buff = IndentingBuffer(target="PsychoPy")

    backend.writeDeviceCode(buff)
    code = buff.getvalue()

    assert "deviceName='netstation'" in code
    assert "ip='10.0.0.42'" in code
    assert "port=55513" in code
    assert "autoDrift=True" in code
    assert "autoDriftBackground=True" in code
    assert "deviceManager.getDevice('netstation').connect()" in code
    compile(code, "<generated EGI device code>", "exec")

    template = EGINetStationDeviceBackend.getTemplateJSON()
    assert template["label"] == "EGI NetStation"
    assert template["device"].endswith(".EGINetStation")


def test_device_manager_connects_before_component_initialization(routine):
    from psychopy import prefs

    backend = EGINetStationDeviceBackend({
        "deviceName": "EGI NetStation (manual configuration)",
        "ip": "10.0.0.42",
        "port": 55513,
        "ntpIP": "10.0.0.51",
        "endian": "NTEL",
    })
    backend.params["name"].val = "netstation"
    previous = prefs.devices.get("netstation")
    prefs.devices["netstation"] = backend
    try:
        component = EgiStartRecordingComponent(
            routine.exp,
            routine.name,
            deviceLabel="netstation",
            measureRefresh=False,
        )
        routine.addComponent(component)
        script = routine.exp.writeScript(expPath=None)
    finally:
        if previous is None:
            prefs.devices.pop("netstation", None)
        else:
            prefs.devices["netstation"] = previous

    connect = "deviceManager.getDevice('netstation').connect()"
    componentInit = "_egiStartRecordingDevice = deviceManager.getDevice('netstation')"
    assert script.index(connect) < script.index(componentInit)
    compile(script, "<integrated EGI Device Manager script>", "exec")


def test_init_component_remains_available_for_old_experiments(routine):
    comp = NetStationInitComponent(
        routine.exp, routine.name,
        name="netStationInit",
        deviceLabel="netstation",
        ip="10.0.0.42",
        port=55513,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "deviceClass='psychopy_egi_pynetstation.hardware.netstation.EGINetStation'" in script
    assert "deviceName='netstation'" in script
    assert "ip='10.0.0.42'" in script


def test_connect_component_writes_connect_call(routine):
    comp = EgiConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "_egiConnectDevice = deviceManager.getDevice('netstation')" in script
    assert "egiConnect = _NetStationComponentState(" in script
    assert "egiConnect.connect()" in script


def test_components_in_one_routine_get_independent_lifecycle_state(routine):
    components = [
        EgiStartRecordingComponent(
            routine.exp, routine.name,
            name="egiStartRecording", deviceLabel="netstation", startVal=1.0,
            measureRefresh=False,
        ),
        EgiSendEventComponent(
            routine.exp, routine.name,
            name="egiSendEvent", deviceLabel="netstation", startVal=2.0,
            eventType="stim",
        ),
    ]
    for component in components:
        routine.addComponent(component)

    script = routine.exp.writeScript(expPath=None)

    assert (
        "from psychopy_egi_pynetstation.component_state import "
        "NetStationComponentState as _NetStationComponentState"
    ) in script
    for name in ("egiStartRecording", "egiSendEvent"):
        assert f"_{name}Device = deviceManager.getDevice('netstation')" in script
        assert f"{name} = _NetStationComponentState(" in script
        assert f"_{name}Device, status=NOT_STARTED" in script
    # Begin Recording may block. Re-reading the Routine clocks lets
    # an overdue later marker still run in the current loop iteration rather
    # than being skipped when the Routine deadline is reached.
    assert script.count(
        "# refresh Routine clocks after the blocking NetStation command"
    ) == 1
    compile(script, "<generated EGI script>", "exec")


def test_plain_numeric_start_with_leading_zero_is_normalized(routine):
    comp = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        deviceLabel="netstation",
        startVal="04",
        eventType="stim",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    compile(script, "<generated EGI script>", "exec")
    assert "tThisFlip >= 4-frameTolerance" in script


def test_start_expression_is_not_normalized(routine):
    comp = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        deviceLabel="netstation",
        startVal="$eventTime",
        eventType="stim",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "tThisFlip >= eventTime-frameTolerance" in script


def test_device_backend_clarifies_endian_options():
    comp = EGINetStationDeviceBackend({"deviceName": None})

    labels = comp.params["endian"].allowedLabels
    hint = comp.params["endian"].hint

    assert "NTEL - little-endian" in labels[0]
    assert "Apple Silicon" in labels[0]
    assert "MAC- - big-endian" in labels[1]
    assert "PowerPC" in labels[1]
    assert "UNIX - big-endian" in labels[2]
    assert "not most modern Linux" in labels[2]
    assert "legacy big-endian" in hint


@pytest.mark.parametrize("component,options,expected", [
    (EgiConnectComponent, {}, ["connect"]),
    (EgiConnectComponent, {"askOnFailure": True}, ["connect"]),
    (EgiDisconnectComponent, {}, ["disconnect"]),
    (EgiStartRecordingComponent, {}, ["beginRecording"]),
    (EgiStartRecordingComponent, {"waitForDrift": True},
     ["beginRecording", "waitForDrift"]),
    (EgiStopRecordingComponent, {}, ["endRecording"]),
])
@pytest.mark.parametrize("fails", [False, True])
def test_one_shot_commands_finish_only_after_success(routine, component, options, expected, fails):
    from types import SimpleNamespace
    from psychopy_egi_pynetstation.component_state import NetStationComponentState

    comp = component(routine.exp, routine.name, name="command", **options)
    buff = IndentingBuffer()
    comp.writeCommandCode(buff)
    calls = []

    def record(name):
        def run(**kwargs):
            assert command.status == "STARTED"
            calls.append(name)
            if fails and name == expected[-1]:
                raise RuntimeError("command failed")
        return run

    device = SimpleNamespace(**{name: record(name) for name in expected})
    command = NetStationComponentState(device, status="STARTED")
    namespace = {
        "command": command, "FINISHED": "FINISHED", "_nsAskFailure": object(),
        "logging": SimpleNamespace(info=lambda message: None),
    }
    if fails:
        with pytest.raises(RuntimeError, match="command failed"):
            exec(buff.getvalue(), namespace)
        assert command.status == "STARTED"
    else:
        exec(buff.getvalue(), namespace)
        assert command.status == "FINISHED"
    assert calls == expected


def test_disconnect_component_writes_disconnect_call(routine):
    comp = EgiDisconnectComponent(
        routine.exp, routine.name,
        name="egiDisconnect",
        deviceLabel="netstation",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiDisconnect.disconnect()" in script


def test_start_recording_component_writes_begin_recording(routine):
    comp = EgiStartRecordingComponent(
        routine.exp, routine.name,
        name="egiStartRecording",
        deviceLabel="netstation",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiStartRecording.beginRecording()" in script
    assert "egiStartRecording.waitForDrift(" not in script


def test_start_recording_component_can_wait_for_drift(routine):
    comp = EgiStartRecordingComponent(
        routine.exp, routine.name,
        name="egiStartRecording",
        deviceLabel="netstation",
        waitForDrift=True,
        driftWaitTimeout=45.0,
        driftWaitPoll=0.25,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiStartRecording.beginRecording()" in script
    assert "Waiting for NetStation drift correction to become ready." in script
    assert "egiStartRecording.waitForDrift(" in script
    assert "timeout=45.0" in script
    assert "poll=0.25" in script
    assert "logging.info(" in script
    assert any(
        required.importName == "logging"
        and required.importFrom == "psychopy"
        for required in comp.exp.requiredImports
    )
    assert comp.params["waitForDrift"].categ == "Drift"
    compile(script, "<generated drift wait EGI script>", "exec")


def test_stop_recording_component_writes_end_recording(routine):
    comp = EgiStopRecordingComponent(
        routine.exp, routine.name,
        name="egiStopRecording",
        deviceLabel="netstation",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiStopRecording.endRecording()" in script


def test_send_event_component_syncs_to_flip_by_default(routine):
    comp = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        deviceLabel="netstation",
        eventType="stim",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    # timestamped on the flip which actually shows the stimulus
    assert "win.callOnFlip(" in script
    assert "egiSendEvent.sendEvent," in script
    assert "eventType='stim'" in script
    assert comp.params["eventDuration"].val == 0.1
    assert "duration=0.1" in script


def test_send_event_component_direct_call_when_not_syncing(routine):
    comp = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        deviceLabel="netstation",
        eventType="resp",
        syncScreenRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiSendEvent.sendEvent(" in script
    assert "start='now'" in script


@pytest.mark.parametrize("sync", [False, True])
def test_send_event_finishes_after_dispatch(routine, sync):
    from types import SimpleNamespace
    from psychopy_egi_pynetstation.component_state import NetStationComponentState

    comp = EgiSendEventComponent(
        routine.exp, routine.name, name="marker", syncScreenRefresh=sync,
    )
    buff = IndentingBuffer()
    comp.writeCommandCode(buff)
    calls = []
    callbacks = []

    def send_event(**kwargs):
        assert marker.status == "STARTED"
        calls.append(kwargs)

    marker = NetStationComponentState(
        SimpleNamespace(sendEvent=send_event), status="STARTED",
    )
    win = SimpleNamespace(
        callOnFlip=lambda fn, *args, **kwargs: callbacks.append((fn, args, kwargs)),
    )
    exec(buff.getvalue(), {"marker": marker, "win": win, "FINISHED": "FINISHED"})
    if sync:
        assert marker.status == "STARTED"
        assert calls == []
        for fn, args, kwargs in callbacks:
            fn(*args, **kwargs)
    assert marker.status == "FINISHED"
    assert len(calls) == 1


def test_send_event_target_is_studio_safe_text_field(routine):
    stimulus = TextComponent(
        routine.exp, routine.name,
        name="stimulus",
        text="hello",
    )
    connect = EgiConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        measureRefresh=False,
    )
    marker = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
    )
    for component in (stimulus, connect, marker):
        routine.addComponent(component)

    target = marker.params["targetComponent"]
    assert target.inputType == "single"
    assert target.valType == "str"
    assert target.allowedVals == []
    assert target.allowedLabels == []
    assert {
        "dependsOn": "targetComponent",
        "condition": "!= ''",
        "param": "start",
        "true": "disable",
        "false": "enable",
    } in marker.depends


def test_send_event_target_param_serializes_without_bound_methods():
    target = EgiSendEventComponent.getTemplateJSON()["params"]["targetComponent"]

    assert target["allowedVals"] == []
    assert target["allowedLabels"] == []


def test_send_event_can_bind_to_visual_component_start(routine):
    stimulus = TextComponent(
        routine.exp, routine.name,
        name="stimulus",
        text="hello",
        startVal=1.5,
    )
    marker = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        targetComponent="stimulus",
        startVal=99,
        syncScreenRefresh=False,
        eventType="stim",
    )
    routine.addComponent(stimulus)
    routine.addComponent(marker)

    script = routine.exp.writeScript(expPath=None)

    assert (
        "if egiSendEvent.status == NOT_STARTED and "
        "stimulus.status == STARTED:" in script
    )
    assert "# queue this marker on the first flip which draws stimulus" in script
    assert "win.callOnFlip(setattr, egiSendEvent, 'status', FINISHED)" in script
    assert "win.callOnFlip(" in script
    assert "egiSendEvent.sendEvent," in script
    assert "thisExp.timestampOnFlip(win, 'egiSendEvent.started')" in script
    assert "tThisFlip >= 99-frameTolerance" not in script
    assert "start='now'" not in script
    compile(script, "<generated target-bound EGI script>", "exec")


def test_send_event_rejects_target_below_marker(routine):
    marker = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        targetComponent="stimulus",
    )
    stimulus = TextComponent(
        routine.exp, routine.name,
        name="stimulus",
        text="hello",
    )
    routine.addComponent(marker)
    routine.addComponent(stimulus)

    with pytest.raises(CodeGenerationException, match="must be below its target"):
        routine.exp.writeScript(expPath=None)


def test_send_event_rejects_missing_target(routine):
    marker = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        targetComponent="renamedStimulus",
    )
    routine.addComponent(marker)

    with pytest.raises(CodeGenerationException, match="does not exist"):
        routine.exp.writeScript(expPath=None)


def test_send_event_rejects_disabled_target(routine):
    stimulus = TextComponent(
        routine.exp, routine.name,
        name="stimulus",
        text="hello",
    )
    stimulus.params["disabled"].val = True
    marker = EgiSendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        targetComponent="stimulus",
    )
    routine.addComponent(stimulus)
    routine.addComponent(marker)

    with pytest.raises(
        CodeGenerationException, match="does not exist or is disabled"
    ):
        routine.exp.writeScript(expPath=None)


# --- Device backend: drift modes ---


@pytest.mark.parametrize("mode,autoDrift,background", [
    ("background", "True", "True"),
    ("off", "False", "False"),
])
def test_device_backend_translates_drift_mode(mode, autoDrift, background):
    comp = EGINetStationDeviceBackend({"deviceName": None})
    comp.params["name"].val = "netstation"
    comp.params["driftMode"].val = mode
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeDeviceCode(buff)
    script = buff.getvalue()

    assert f"autoDrift={autoDrift}" in script
    assert f"autoDriftBackground={background}" in script
    assert "ntpIP='10.10.10.51'" in script


def test_device_backend_defaults_to_background_drift():
    comp = EGINetStationDeviceBackend({"deviceName": None})
    comp.params["name"].val = "netstation"
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeDeviceCode(buff)
    script = buff.getvalue()

    assert "autoDrift=True" in script
    assert "autoDriftBackground=True" in script
    assert "driftWarmup=False" in script


@pytest.mark.parametrize("warmup,expected", [(False, "False"), (True, "True")])
def test_device_backend_forwards_drift_warmup(warmup, expected):
    comp = EGINetStationDeviceBackend({"deviceName": None})
    comp.params["name"].val = "netstation"
    comp.params["driftWarmup"].val = warmup
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeDeviceCode(buff)
    script = buff.getvalue()

    assert f"driftWarmup={expected}" in script
    assert comp.params["driftWarmup"].categ == "Drift"


def test_device_backend_disables_warmup_with_drift_off():
    comp = EGINetStationDeviceBackend({"deviceName": None})
    comp.params["name"].val = "netstation"
    comp.params["driftMode"].val = "off"
    comp.params["driftWarmup"].val = True
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeDeviceCode(buff)
    script = buff.getvalue()

    assert "driftWarmup=False" in script


@pytest.mark.parametrize("strict,expected", [(False, "False"), (True, "True")])
def test_device_backend_forwards_strict_eci(strict, expected):
    comp = EGINetStationDeviceBackend({"deviceName": None})
    comp.params["name"].val = "netstation"
    comp.params["strictECI"].val = strict
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeDeviceCode(buff)
    script = buff.getvalue()

    assert f"strictECI={expected}" in script
    assert comp.params["strictECI"].categ == "Data"


def test_device_backend_no_longer_passes_async_events():
    # upstream dropped connect(async_events=...); make sure we don't resurrect it
    comp = EGINetStationDeviceBackend({"deviceName": None})
    comp.params["name"].val = "netstation"
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeDeviceCode(buff)
    script = buff.getvalue()

    assert "asyncEvents" not in script


# --- Start Recording: display timing ---


def test_display_timing_measures_and_records(routine):
    comp = EgiStartRecordingComponent(
        routine.exp, routine.name,
        name="egiStartRecording", deviceLabel="netstation",
        measureRefresh=True,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "_nsTiming.measureDisplay(win)" in script
    assert ".logDisplayTiming(" in script
    # the module must actually be imported, or the script is broken
    assert "import timing as _nsTiming" in script


def test_display_timing_can_be_switched_off(routine):
    comp = EgiStartRecordingComponent(
        routine.exp, routine.name,
        name="egiStartRecording", deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "measureDisplay" not in script


def test_schedule_check_skips_routines_with_no_fixed_duration(routine):
    """
    A Routine ended by a keypress has no fixed interval, so there is nothing
    for a beat to build against. Skipping it is correct, not a limitation.
    """
    comp = EgiStartRecordingComponent(
        routine.exp, routine.name,
        name="egiStartRecording", deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    # the Routine holds only our momentary Component, so nothing is resolvable
    assert comp._harvestSchedule() == {}

    script = routine.exp.writeScript(expPath=None)
    assert "describeSchedule" not in script


def test_component_end_resolution():
    cls = EgiStartRecordingComponent
    from psychopy.experiment.params import Param

    def comp(startVal, stopVal, stopType):
        return type("C", (), {"type": "Text", "params": {
            "startType": Param("time (s)", valType="str"),
            "startVal": Param(startVal, valType="code"),
            "stopType": Param(stopType, valType="str"),
            "stopVal": Param(stopVal, valType="code"),
        }})()

    assert cls._componentEnd(comp(0.5, 2.0, "duration (s)")) == 2.5
    assert cls._componentEnd(comp(0.0, 3.0, "time (s)")) == 3.0
    # frame units, blank stops and variables are all not statically knowable
    assert cls._componentEnd(comp(0.0, 180, "duration (frames)")) is None
    assert cls._componentEnd(comp(0.0, "", "duration (s)")) is None
    assert cls._componentEnd(comp(0.0, "$myVar", "duration (s)")) is None


@pytest.mark.parametrize('enabled', [False, True])
def test_both_setup_paths_forward_dummy_mode(routine, enabled):
    legacy = NetStationInitComponent(routine.exp, routine.name, dummyMode=enabled,
                                     measureRefresh=False)
    backend = EGINetStationDeviceBackend({'deviceName': None, 'dummyMode': enabled})
    backend.params['name'].val = 'netstation'
    for comp, writer in [(legacy, legacy.writeInitCode), (backend, backend.writeDeviceCode)]:
        buff = IndentingBuffer(target='PsychoPy')
        writer(buff)
        script = buff.getvalue()
        assert f'dummyMode={enabled}' in script
        assert comp.params['dummyMode'].categ == 'Device'
        compile(script, '<dummy setup>', 'exec')


@pytest.mark.parametrize('legacy', [False, True])
def test_startup_mode_is_in_expinfo_before_device_creation(routine, legacy):
    import ast
    from psychopy import prefs
    from psychopy_egi_pynetstation.startup import DUMMY_MODE, REAL_MODE, modeKey

    original_info = routine.exp.settings.params['Experiment info'].val
    backend = EGINetStationDeviceBackend({'deviceName': None, 'chooseAtStartup': True,
                                         'askOnFailure': True})
    backend.params['name'].val = 'netstation'
    previous = prefs.devices.get('netstation')
    prefs.devices['netstation'] = backend
    try:
        if legacy:
            comp = EgiConnectComponent(routine.exp, routine.name, chooseAtStartup=True,
                                       askOnFailure=True, measureRefresh=False)
        else:
            comp = EgiStartRecordingComponent(routine.exp, routine.name, deviceLabel="netstation", measureRefresh=False)
        routine.addComponent(comp)
        # Multiple consumers must not produce duplicate fields or mutate saved settings.
        if not legacy:
            routine.addComponent(EgiStopRecordingComponent(routine.exp, routine.name, deviceLabel="netstation"))
        script = routine.exp.writeScript(expPath=None)
    finally:
        if previous is None:
            prefs.devices.pop('netstation', None)
        else:
            prefs.devices['netstation'] = previous
    tree = ast.parse(script)
    info_assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == 'expInfo' for t in node.targets))
    fields = {ast.literal_eval(k): v for k, v in zip(info_assignment.value.keys, info_assignment.value.values)}
    assert ast.literal_eval(fields[modeKey('netstation')]) == [REAL_MODE, DUMMY_MODE]
    assert 'dummyMode=_nsResolveMode(expInfo,' in script
    assert '.connect(onFailure=_nsAskFailure)' in script
    assert '.setRunInfo(expInfo,' in script
    assert routine.exp.settings.params['Experiment info'].val == original_info
    assert not backend.params['dummyMode']
    compile(script, '<startup integration>', 'exec')


def test_generated_setup_honors_dummy_choice_before_constructing_client(monkeypatch):
    from psychopy_egi_pynetstation.hardware.netstation import EGINetStation
    from psychopy_egi_pynetstation.startup import DUMMY_MODE, modeKey

    monkeypatch.setattr('psychopy_egi_pynetstation.hardware.netstation.NetStation',
                        lambda *args, **kwargs: pytest.fail('real client constructed'))
    class Manager:
        def addDevice(self, deviceClass, deviceName, **kwargs):
            self.device = EGINetStation(**kwargs)
        def getDevice(self, name):
            return self.device
    backend = EGINetStationDeviceBackend({'deviceName': None, 'chooseAtStartup': True,
                                         'askOnFailure': True})
    backend.params['name'].val = 'netstation'
    buff = IndentingBuffer(target='PsychoPy')
    backend.writeDeviceCode(buff)
    manager = Manager()
    info = {modeKey('netstation'): DUMMY_MODE}
    exec(buff.getvalue(), {'deviceManager': manager, 'expInfo': info})
    assert manager.device.dummyMode
    assert info['netstation.netstation.effective_mode'] == 'dummy'
    manager.device.close()


def test_legacy_init_passes_recovery_callback(routine):
    comp = NetStationInitComponent(routine.exp, routine.name, askOnFailure=True,
                                    measureRefresh=False)
    buff = IndentingBuffer(target='PsychoPy')
    comp.writeInitCode(buff)
    assert 'onConnectionFailure=_nsAskFailure if True else None' in buff.getvalue()


def test_startup_fields_keep_devices_separate_and_default_modes(routine):
    import ast
    from psychopy_egi_pynetstation.components._startup import addStartupField
    from psychopy_egi_pynetstation.startup import DUMMY_MODE, REAL_MODE, modeKey
    for name, dummy in [('a', False), ('b', True)]:
        backend = EGINetStationDeviceBackend({'deviceName': None, 'chooseAtStartup': True,
                                             'dummyMode': dummy})
        addStartupField(routine.exp, name, backend.params)
        addStartupField(routine.exp, name, backend.params)
    info = ast.literal_eval(routine.exp.settings.params['Experiment info'].val)
    assert info[modeKey('a')] == [REAL_MODE, DUMMY_MODE]
    assert info[modeKey('b')] == [DUMMY_MODE, REAL_MODE]
    assert 'participant' in info
