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
)
from psychopy_egi_pynetstation.components.netStationDisconnect import (  # noqa: E402
    EGIDisconnectComponent,
)
from psychopy_egi_pynetstation.components.netStationStartRecording import (  # noqa: E402
    EGIStartRecordingComponent,
)
from psychopy_egi_pynetstation.components.netStationStopRecording import (  # noqa: E402
    EGIStopRecordingComponent,
)
from psychopy_egi_pynetstation.components.netStationSendEvent import (  # noqa: E402
    EGISendEventComponent,
)


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
        "EgiConnectComponent",
        "EgiStartRecordingComponent",
        "EgiStopRecordingComponent",
        "EgiDisconnectComponent",
        "EgiSendEventComponent",
    }


def test_builder_component_names_include_egi_word_break():
    from psychopy.tools import stringtools as st

    assert st.CaseSwitcher.pascal2title(EGIConnectComponent.__name__).startswith("Egi Connect")
    assert st.CaseSwitcher.pascal2title(EGISendEventComponent.__name__).startswith("Egi Send Event")


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
    assert "egiConnect = deviceManager.getDevice('netstation')" in script
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

    assert "egiConnect = deviceManager.getDevice('netstation')" in script
    assert "egiConnect.connect()" in script


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
    # event sends are async and can't raise, so the run must report failures
    assert ".eventErrors()" in script


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
