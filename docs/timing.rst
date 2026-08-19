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

Display refresh and the frame beat
----------------------------------

A display refreshes on a fixed heartbeat. If a clock-timed Routine duration is
not an exact whole number of refresh periods, its requested onset slowly moves
through the refresh cycle. Because presentation can happen only on a frame
boundary, that movement can eventually appear as a one-frame step.

This is a stimulus-presentation effect, not an ECI marker error. The plugin
measures and reports the risk; it does not reschedule an experiment.

EGI Connect's **Measure display refresh at startup** option measures the real
rate once during setup. If measurement fails, the code uses PsychoPy's monitor
frame period and finally falls back to 60 Hz with a warning. The exact measured
value matters: a monitor near, but not exactly at, 60 Hz can produce a slow
phase sweep that would be invisible under a 60.000 Hz assumption.

With **Warn about vulnerable schedules** enabled, fixed Routine durations are
harvested when Builder generates the experiment. Durations are weighted by how
often their Routines run. Response-terminated, variable, and otherwise
indeterminate Routines are skipped.

If a warning matters for the experiment, specify the relevant Builder
durations in frames. Frame counting removes the systematic phase sweep, but it
changes the exact interval and dropped frames accumulate rather than
self-correct. Validate the choice against the scientific timing requirements.

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
