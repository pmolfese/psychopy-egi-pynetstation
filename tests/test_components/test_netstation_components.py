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
from psychopy_egi_pynetstation.components.netStationConnect import (  # noqa: E402
    EGIConnectComponent,
    EgiConnectComponent,
)
from psychopy_egi_pynetstation.components.netStationDisconnect import (  # noqa: E402
    EGIDisconnectComponent,
    EgiDisconnectComponent,
)
from psychopy_egi_pynetstation.components.netStationStartRecording import (  # noqa: E402
    EGIStartRecordingComponent,
    EgiStartRecordingComponent,
)
from psychopy_egi_pynetstation.components.netStationStopRecording import (  # noqa: E402
    EGIStopRecordingComponent,
    EgiStopRecordingComponent,
)
from psychopy_egi_pynetstation.components.netStationSendEvent import (  # noqa: E402
    EGISendEventComponent,
    EgiSendEventComponent,
)
from psychopy.experiment.components.text import TextComponent  # noqa: E402
from psychopy.experiment.utils import CodeGenerationException  # noqa: E402


@pytest.fixture
def routine():
    exp = Experiment()
    exp.addRoutine("trial")
    exp.flow.addRoutine(exp.routines["trial"], pos=0)
    return exp.routines["trial"]


def test_plugin_exposes_only_visible_builder_components():
    names = {
        ep.name
        for ep in entry_points(group="psychopy.experiment.components")
        if ep.value.startswith("psychopy_egi_pynetstation.")
    }

    assert names == {
        "EGIConnectComponent",
        "EGIStartRecordingComponent",
        "EGIStopRecordingComponent",
        "EGIDisconnectComponent",
        "EGISendEventComponent",
    }


def test_builder_component_names_use_uppercase_egi():
    from psychopy.tools import stringtools as st

    for component_class in (
        EGIConnectComponent,
        EGIStartRecordingComponent,
        EGIStopRecordingComponent,
        EGIDisconnectComponent,
        EGISendEventComponent,
    ):
        label = component_class.__name__.removesuffix("Component")
        label = st.CaseSwitcher.pascal2title(label)
        assert label.startswith("EGI")
        assert not label.startswith("Egi")


def test_previous_component_class_names_remain_importable():
    assert EgiConnectComponent is EGIConnectComponent
    assert EgiStartRecordingComponent is EGIStartRecordingComponent
    assert EgiStopRecordingComponent is EGIStopRecordingComponent
    assert EgiDisconnectComponent is EGIDisconnectComponent
    assert EgiSendEventComponent is EGISendEventComponent


def test_connect_component_registers_device_and_connects(routine):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        ip="10.0.0.42",
        port=55513,
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "deviceClass='psychopy_egi_pynetstation.hardware.netstation.EGINetStation'" in script
    assert "deviceName='netstation'" in script
    assert "ip='10.0.0.42'" in script
    assert "_egiConnectDevice = deviceManager.getDevice('netstation')" in script
    assert "egiConnect = _NetStationComponentState(" in script
    assert "egiConnect.connect()" in script


@pytest.mark.parametrize("componentClass", [
    EGIConnectComponent,
    EGIStartRecordingComponent,
    EGIStopRecordingComponent,
    EGIDisconnectComponent,
    EGISendEventComponent,
])
def test_device_label_is_manual_text_not_device_manager_selector(
    routine, componentClass
):
    comp = componentClass(routine.exp, routine.name, deviceLabel="netstation")

    label = comp.params["deviceLabel"]
    assert label.val == "netstation"
    assert label.valType == "str"
    assert label.inputType == "single"
    assert "not a Device Manager selection" in label.hint

    # Old .psyexp files saved this as valType="device". PsychoPy applies that
    # metadata during load, so the Param must normalize it back to plain text.
    label.valType = "device"
    assert label.valType == "str"


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
    comp = EGIConnectComponent(
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
        EGIConnectComponent(
            routine.exp, routine.name,
            name="egiConnect", deviceLabel="netstation", measureRefresh=False,
        ),
        EGIStartRecordingComponent(
            routine.exp, routine.name,
            name="egiStartRecording", deviceLabel="netstation", startVal=1.0,
        ),
        EGISendEventComponent(
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
    for name in ("egiConnect", "egiStartRecording", "egiSendEvent"):
        assert f"_{name}Device = deviceManager.getDevice('netstation')" in script
        assert f"{name} = _NetStationComponentState(" in script
        assert f"_{name}Device, status=NOT_STARTED" in script
    # Connect and Begin Recording may block. Re-reading the Routine clocks lets
    # an overdue later marker still run in the current loop iteration rather
    # than being skipped when the Routine deadline is reached.
    assert script.count(
        "# refresh Routine clocks after the blocking NetStation command"
    ) == 2
    compile(script, "<generated EGI script>", "exec")


def test_connect_component_uses_default_lab_addresses(routine):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "ip='10.10.10.42'" in script
    assert "ntpIP='10.10.10.51'" in script
    assert "port=55513," in script
    assert "port=55513.0" not in script


def test_plain_numeric_start_with_leading_zero_is_normalized(routine):
    comp = EGISendEventComponent(
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
    comp = EGISendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        deviceLabel="netstation",
        startVal="$eventTime",
        eventType="stim",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "tThisFlip >= eventTime-frameTolerance" in script


def test_connect_component_clarifies_endian_options(routine):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        measureRefresh=False,
    )

    labels = comp.params["endian"].allowedLabels
    hint = comp.params["endian"].hint

    assert "NTEL - little-endian" in labels[0]
    assert "Apple Silicon" in labels[0]
    assert "MAC- - big-endian" in labels[1]
    assert "PowerPC" in labels[1]
    assert "UNIX - big-endian" in labels[2]
    assert "not most modern Linux" in labels[2]
    assert "misleading for most modern Unix/Linux" in hint


def test_disconnect_component_writes_disconnect_call(routine):
    comp = EGIDisconnectComponent(
        routine.exp, routine.name,
        name="egiDisconnect",
        deviceLabel="netstation",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiDisconnect.disconnect()" in script


def test_start_recording_component_writes_begin_recording(routine):
    comp = EGIStartRecordingComponent(
        routine.exp, routine.name,
        name="egiStartRecording",
        deviceLabel="netstation",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiStartRecording.beginRecording()" in script
    assert "egiStartRecording.waitForDrift(" not in script


def test_start_recording_component_can_wait_for_drift(routine):
    comp = EGIStartRecordingComponent(
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
    assert "from psychopy import logging" in script
    assert comp.params["waitForDrift"].categ == "Drift"
    compile(script, "<generated drift wait EGI script>", "exec")


def test_stop_recording_component_writes_end_recording(routine):
    comp = EGIStopRecordingComponent(
        routine.exp, routine.name,
        name="egiStopRecording",
        deviceLabel="netstation",
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "egiStopRecording.endRecording()" in script


def test_send_event_component_syncs_to_flip_by_default(routine):
    comp = EGISendEventComponent(
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
    comp = EGISendEventComponent(
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


def test_send_event_target_selector_lists_visual_components_only(routine):
    stimulus = TextComponent(
        routine.exp, routine.name,
        name="stimulus",
        text="hello",
    )
    connect = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        measureRefresh=False,
    )
    marker = EGISendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
    )
    for component in (stimulus, connect, marker):
        routine.addComponent(component)

    assert marker.getTargetComponentVals() == ["", "stimulus"]
    assert marker.getTargetComponentLabels() == [
        "Use this marker's Start settings",
        "stimulus (Text)",
    ]
    assert {
        "dependsOn": "targetComponent",
        "condition": "!= ''",
        "param": "start",
        "true": "disable",
        "false": "enable",
    } in marker.depends


def test_send_event_can_bind_to_visual_component_start(routine):
    stimulus = TextComponent(
        routine.exp, routine.name,
        name="stimulus",
        text="hello",
        startVal=1.5,
    )
    marker = EGISendEventComponent(
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
    assert "win.callOnFlip(" in script
    assert "egiSendEvent.sendEvent," in script
    assert "thisExp.timestampOnFlip(win, 'egiSendEvent.started')" in script
    assert "tThisFlip >= 99-frameTolerance" not in script
    assert "start='now'" not in script
    compile(script, "<generated target-bound EGI script>", "exec")


def test_send_event_rejects_target_below_marker(routine):
    marker = EGISendEventComponent(
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
    marker = EGISendEventComponent(
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
    marker = EGISendEventComponent(
        routine.exp, routine.name,
        name="egiSendEvent",
        targetComponent="stimulus",
    )
    routine.addComponent(stimulus)
    routine.addComponent(marker)

    assert marker.getTargetComponentVals() == [""]
    with pytest.raises(CodeGenerationException, match="is disabled"):
        routine.exp.writeScript(expPath=None)


# --- Connect: drift modes ---


@pytest.mark.parametrize("mode,autoDrift,background", [
    ("background", "True", "True"),
    ("off", "False", "False"),
])
def test_connect_component_translates_drift_mode(routine, mode, autoDrift, background):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        ip="10.10.10.42",
        ntpIP="10.10.10.51",
        driftMode=mode,
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert f"autoDrift={autoDrift}" in script
    assert f"autoDriftBackground={background}" in script
    assert "ntpIP='10.10.10.51'" in script
    # normal and early experiment exits must both reach idempotent cleanup
    assert "runAtExit.append(_egiConnectCleanupDevice.close)" in script
    assert "_egiConnectDevice.close()" in script


def test_connect_component_defaults_to_background_drift(routine):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "autoDrift=True" in script
    assert "autoDriftBackground=True" in script


@pytest.mark.parametrize("strict,expected", [(False, "False"), (True, "True")])
def test_connect_component_forwards_strict_eci(routine, strict, expected):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        strictECI=strict,
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert f"strictECI={expected}" in script
    assert comp.params["strictECI"].categ == "Data"


def test_connect_component_no_longer_passes_async_events(routine):
    # upstream dropped connect(async_events=...); make sure we don't resurrect it
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect",
        deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "asyncEvents" not in script


# --- Connect: display timing ---


def test_display_timing_measures_and_records(routine):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect", deviceLabel="netstation",
        measureRefresh=True,
    )
    routine.addComponent(comp)

    script = routine.exp.writeScript(expPath=None)

    assert "_nsTiming.measureDisplay(win)" in script
    assert ".logDisplayTiming(" in script
    # the module must actually be imported, or the script is broken
    assert "import timing as _nsTiming" in script


def test_display_timing_can_be_switched_off(routine):
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect", deviceLabel="netstation",
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
    comp = EGIConnectComponent(
        routine.exp, routine.name,
        name="egiConnect", deviceLabel="netstation",
        measureRefresh=False,
    )
    routine.addComponent(comp)

    # the Routine holds only our momentary Component, so nothing is resolvable
    assert comp._harvestSchedule() == {}

    script = routine.exp.writeScript(expPath=None)
    assert "describeSchedule" not in script


def test_component_end_resolution():
    cls = EGIConnectComponent
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
