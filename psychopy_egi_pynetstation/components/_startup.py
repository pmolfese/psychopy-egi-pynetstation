"""Shared Builder parameters and compile-time startup-dialog integration."""

import ast

from psychopy.experiment.components import Param
from psychopy_egi_pynetstation.startup import DUMMY_MODE, REAL_MODE, modeKey


def addStartupParams(component, chooseAtStartup=False, askOnFailure=False):
    component.order += ['chooseAtStartup', 'askOnFailure']
    component.params['chooseAtStartup'] = Param(
        chooseAtStartup, valType='bool', inputType='bool', categ='Device',
        label='Choose EEG mode at startup',
        hint='Add a per-run EEG mode choice to the participant/session dialog. '
             'The Dummy mode setting supplies the default.',
    )
    component.params['askOnFailure'] = Param(
        askOnFailure, valType='bool', inputType='bool', categ='Device',
        label='Ask after connection failure',
        hint='During connection setup, offer Abort, Retry, or Continue without EEG. '
             'Does not recover recording or mid-run failures.',
    )


def addStartupField(exp, deviceLabel, params):
    """Modify only Builder's compilation copy, before it writes expInfo.

    Device backends have no pre-code hook. Their consuming EGI components
    register this field during writePreCode, before settings.writeGlobals.
    """
    if not params['chooseAtStartup']:
        return
    infoParam = exp.settings.params['Experiment info']
    info = ast.literal_eval(str(infoParam.val).strip() or '{}')
    key = modeKey(deviceLabel)
    choices = [DUMMY_MODE, REAL_MODE] if params['dummyMode'] else [REAL_MODE, DUMMY_MODE]
    if key in info and info[key] != choices:
        raise ValueError(f'{key!r} is reserved for the NetStation startup selector')
    info[key] = choices
    infoParam.val = repr(info)
