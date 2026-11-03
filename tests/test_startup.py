"""Startup choice resolution and optional dialog behavior without hardware."""

import sys
from types import SimpleNamespace

import pytest

from psychopy_egi_pynetstation.startup import (
    DUMMY_MODE, REAL_MODE, askConnectionFailure, modeKey, resolveDummyMode,
)


@pytest.mark.parametrize('default', [False, True])
def test_missing_or_unsubmitted_dialog_uses_configured_default(default):
    for info in ({}, {modeKey('ns'): [REAL_MODE, DUMMY_MODE]}):
        assert resolveDummyMode(info, 'ns', default, True) is default


def test_selected_mode_overrides_default_only_when_enabled():
    info = {modeKey('ns'): DUMMY_MODE, modeKey('other'): REAL_MODE}
    assert resolveDummyMode(info, 'ns', False, True)
    assert not resolveDummyMode(info, 'ns', False, False)
    assert not resolveDummyMode(info, 'other', True, True)
    info[modeKey('ns')] = 'typo'
    with pytest.raises(ValueError, match='Invalid EEG mode'):
        resolveDummyMode(info, 'ns', False, True)


@pytest.mark.parametrize('choice,ok,expected', [
    ('Abort', True, 'abort'), ('Retry', True, 'retry'),
    ('Continue without EEG', True, 'dummy'), ('Retry', False, 'abort'),
])
@pytest.mark.parametrize('use_dict', [False, True])
def test_failure_dialog_defaults_to_abort_and_honors_cancel(monkeypatch, choice, ok, expected, use_dict):
    class Dialog:
        OK = ok

        def __init__(self, title, alwaysOnTop):
            assert alwaysOnTop
            assert title == 'NetStation connection failed'

        def addText(self, text):
            assert '127.0.0.1:55513' in text
            assert 'No EEG will be recorded' in text

        def addField(self, key, initial, choices):
            assert key == 'Action'
            assert initial == choices[0] == 'Abort'

        def show(self):
            if not ok:
                return None
            return {'Action': choice} if use_dict else [choice]

    monkeypatch.setitem(sys.modules, 'psychopy', SimpleNamespace(gui=SimpleNamespace(Dlg=Dialog)))
    assert askConnectionFailure(ConnectionRefusedError('refused'), '127.0.0.1', 55513) == expected
