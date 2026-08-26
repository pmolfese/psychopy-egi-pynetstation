Timing and event synchronization
================================

Flip-synchronized markers
-------------------------

For a marker tied to a visual stimulus, keep EGI Send Event's **Sync to screen
refresh** option enabled. Builder generates a ``win.callOnFlip`` callback, so
the event timestamp is captured on the flip that presents the stimulus. Event
transmission is asynchronous and does not wait for the amplifier inside the
flip callback.

Turn synchronization off for a nonvisual event that should be timestamped as
soon as its Builder Component starts. In that mode the generated call uses
``start='now'`` directly.

Synchronizing to one named Builder stimulus
--------------------------------------------

When a marker should follow the onset of one particular Builder stimulus,
choose that stimulus in EGI Send Event's **Target visual Component** field.
Only visual Components in the same Routine appear in the selector. Put EGI
Send Event *below the target stimulus* in the Routine: Builder then sees the
target change to ``STARTED`` and queues the marker before the same upcoming
window flip draws it. Code generation stops with an explanatory error if the
marker is above its target, because silently continuing would put the event one
screen refresh late.

Selecting a target disables the marker's own **Start** controls. The target
determines when it fires and target binding is always flip synchronized,
regardless of the **Sync to screen refresh** setting. The marker is already
one-shot, so it fires only once per Routine repeat. Leave the target blank to
use the marker's ordinary Start settings instead.

For custom logic beyond the target selector, use a Code Component. This is the
status-guard pattern from PsychoPy's `EGI NetStation guide
<https://psychopy.org/hardware/egiNetStation.html>`_, adapted to this plugin's
API.

First, place the Code Component *below the stimulus* in the same Routine.
Builder runs **Each Frame** code in Component order, so the stimulus must update
its status before the guard is evaluated. In the Code Component's **Begin
Routine** tab, retrieve the client registered by EGI Connect and reset the
one-shot guard::

   eci_client = deviceManager.getDevice("netstation")
   if eci_client is None:
       raise RuntimeError("No NetStation device named 'netstation'")
   triggerSent = False

Change ``"netstation"`` if EGI Connect uses a different **Device label**. Then
put the following in **Each Frame**::

   if stimulus.status == STARTED and not triggerSent:
       win.callOnFlip(
           eci_client.sendEvent,
           eventType="stim",
           label="stimulus onset",
           duration=0.1,
       )
       triggerSent = True

Replace ``stimulus`` with the **Name** of the visual Component to follow, and
replace ``"stim"`` with the experiment's four-character NetStation event type.
The condition becomes true on the frame where that Component starts. Because
the Code Component is below it, ``callOnFlip`` still queues the marker before
the upcoming flip that first draws the stimulus. ``triggerSent`` is set as soon
as the callback is queued so the marker is not queued again on every later
frame for which the stimulus remains ``STARTED``; it is reset on every Routine
repeat.

The older guide calls the upstream library's ``send_event`` method with an
``event_type`` keyword. Code using this plugin should instead call the
PsychoPy-facing ``sendEvent`` method with ``eventType``, as above. A per-Routine
``resync()`` call is not normally needed because EGI Start Recording establishes
the timestamp epoch and the plugin's default background drift correction keeps
sampling it. Event transmission remains asynchronous, and session cleanup
reports any worker or ECI-response failure.

Display refresh and the frame beat
----------------------------------

A visual stimulus cannot avoid a display refresh: a new image can appear only
when the display refreshes. The practical goal is to make repeated visual
intervals contain a whole number of refreshes. That prevents a requested onset
from slowly moving through the refresh cycle and occasionally falling on the
next frame.

For example, a display measured at 59.94 Hz refreshes every 16.683 ms. A
3.000-second interval spans 179.82 frames, which the display cannot present.
Clock-based scheduling must sometimes use 180 frames, and the fractional
0.18-frame mismatch accumulates from trial to trial. The visible result can be
a sudden one-frame step in stimulus onset. A fixed 180-frame interval is
3.003 seconds on that display: slightly different from 3.000 seconds, but it
does not sweep through the refresh phase.

This is a stimulus-presentation effect, not an ECI marker error. The plugin
measures and reports the risk; it does not reschedule an experiment. A marker
sent with **Target visual Component** or ``callOnFlip`` follows the frame that
was actually presented, including any one-frame presentation step. It keeps
the marker aligned to the stimulus but does not remove the underlying step.

How to use the display check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. In EGI Connect's **Display** tab, leave **Measure display refresh at
   startup** and **Warn about vulnerable schedules** enabled. Run the
   experiment on the same computer, display, resolution, and refresh-rate
   setting that will be used for data collection.
2. Read the startup log entry. It reports the measured frequency and frame
   period, for example ``59.9400 Hz, 16.6834 ms/frame (measured)``. A source of
   ``reported`` is a monitor-setting fallback. A source of ``assumed`` means
   measurement failed and the 60 Hz estimate should not be used to approve a
   schedule.
3. Read any schedule warning. It names the repeated Routine duration, its
   fractional-frame mismatch, the approximate time for a one-frame phase
   sweep, and the size of one frame in milliseconds. The interval used by the
   most trials is reported first; a separate line identifies worse rounding in
   a less common interval.
4. Decide whether the visual interval should be controlled by frames or by
   clock time. If consistent frame phase is the priority, convert the desired
   duration to the nearest whole frame count and use that count in Builder. If
   exact elapsed seconds are the priority, retain clock timing and accept that
   the display must occasionally choose an adjacent frame.

Converting a Builder schedule to frames
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a desired interval ``D`` and measured refresh rate ``F``, use
``round(D * F)`` frames. The actual frame-counted interval is then
``frames / F`` seconds. The helper function performs the same conversion::

   from psychopy_egi_pynetstation.timing import framesFor

   measured_hz = 59.94
   frame_period = 1.0 / measured_hz
   n_frames = framesFor(3.0, frame_period)  # 180
   actual_seconds = n_frames * frame_period  # approximately 3.003

In Builder:

* For a visual Component duration, change its **Stop** type from ``duration
  (s)`` to ``duration (frames)`` and enter ``180`` rather than ``3.0``.
* For an onset within a Routine, use **Start** type ``frame N`` when a fixed
  frame offset is appropriate. The first frame is frame 0.
* For a repeated trial Routine, make sure the Component which determines the
  end of the Routine also ends on the intended frame. A later seconds-timed
  Component can still extend the Routine and reintroduce a fractional-frame
  interval.
* Apply the same reasoning to fixation, blank-screen, and inter-trial Routines
  when their durations contribute to the interval between visual onsets.

.. note::

   Do not convert EGI Send Event's **Event duration (s)** to frames. That field
   is metadata describing the marker duration stored by NetStation; it does
   not control a visual onset, a Builder Component lifetime, or a Routine
   duration. Convert the timing fields on the visual, fixation, blank, or other
   Component which controls the interval between displayed frames.

After editing, run the experiment again and inspect the generated schedule and
frame logs. The automatic checker skips explicitly frame-timed Routines because
they have no fractional-frame duration to calculate in seconds. It also cannot
fully assess a Routine which mixes frame timing with variable or clock-timed
end conditions, so the disappearance of a warning alone is not proof that
every interval is controlled as intended.

What the automatic check can and cannot see
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The automatic warning examines fixed Routine durations that Builder can know
when generating the experiment. Durations are weighted by how often their
Routines run. Response-terminated, variable, conditional, and otherwise
indeterminate Routines are skipped; no warning for one of these Routines is not
proof that its timing is frame-aligned.

Frame-counted scheduling removes the systematic fractional-frame sweep, but it
cannot prevent a dropped frame caused by slow drawing, operating-system load,
or the display/compositor path. A dropped frame makes a frame-counted interval
longer rather than allowing it to self-correct against the clock. Use
PsychoPy's frame-interval or dropped-frame logging during development and
validate physical light onset with a photodiode when timing is scientifically
critical.

Timing helper functions
-----------------------

The calculations are available without importing PsychoPy:

.. code-block:: python

   from psychopy_egi_pynetstation.timing import beatSeconds, frameSlip, framesFor

   frame_period = 1.0 / 60.00043
   frameSlip(3.0, frame_period)      # fractional frame mismatch
   beatSeconds(3.0, frame_period)    # seconds for a one-frame phase sweep
   framesFor(3.0, frame_period)      # nearest whole-frame duration

These helpers describe a systematic risk; they cannot guarantee the time at
which a composited display physically emits light. If onset lateness remains
flat while a one-frame step persists, investigate the display/compositor path
rather than ECI marker transmission.
