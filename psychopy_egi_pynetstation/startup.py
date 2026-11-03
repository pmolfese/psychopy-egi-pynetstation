"""Run-specific EEG mode selection and an optional connection recovery dialog."""

REAL_MODE = 'Record EEG'
DUMMY_MODE = 'Dummy — no EEG recorded'


def modeKey(deviceLabel):
    return f'EEG mode ({deviceLabel})'


def resolveDummyMode(expInfo, deviceLabel, dummyMode=False, chooseAtStartup=False):
    """Read the startup choice before constructing any hardware client.

    A list is the unsubmitted Builder dialog default (e.g. a headless run).
    In that case use the configured device setting, without opening a dialog.
    """
    if not chooseAtStartup:
        return bool(dummyMode)
    selected = expInfo.get(modeKey(deviceLabel))
    if selected is None or isinstance(selected, (list, tuple)):
        return bool(dummyMode)
    if selected not in (REAL_MODE, DUMMY_MODE):
        raise ValueError(f'Invalid EEG mode for {deviceLabel}: {selected!r}')
    return selected == DUMMY_MODE


def askConnectionFailure(error, ip, port):
    """Explicitly choose recovery; Cancel/close and the default mean abort.

    This UI callback is opt-in. Coder/headless callers should omit it or
    supply their own callback returning 'retry', 'dummy', or 'abort'.
    """
    from psychopy import gui

    choices = ['Abort', 'Retry', 'Continue without EEG']
    dlg = gui.Dlg(title='NetStation connection failed', alwaysOnTop=True)
    dlg.addText(f'Could not connect to NetStation at {ip}:{port}.\n'
                f'{type(error).__name__}: {error}\n\n'
                'Continue without EEG runs in dummy mode. No EEG will be recorded.')
    dlg.addField('Action', initial=choices[0], choices=choices)
    result = dlg.show()
    if not dlg.OK:
        return 'abort'
    # Recent PsychoPy returns a dict; older supported dialogs may return a list.
    selected = result['Action'] if isinstance(result, dict) else result[0]
    return dict(zip(choices, ['abort', 'retry', 'dummy'])).get(selected, 'abort')
