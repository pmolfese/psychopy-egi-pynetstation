PsychoPy Coder and Python API
=============================

Builder is optional. PsychoPy Coder and other code-only experiments can either
construct the hardware wrapper directly or register it with PsychoPy's Device
Manager. Both approaches return the same ``EGINetStation`` interface. For a
complete window-and-event example, start with :ref:`coder-quick-start`.

Option 1: direct construction
-----------------------------

This is the smallest setup. Importing the wrapper directly does not require an
explicit plugin-activation call:

.. code-block:: python

   from psychopy_egi_pynetstation import EGINetStation

   ns = EGINetStation(
       ip="10.10.10.42",
       ntpIP="10.10.10.51",
       port=55513,
   )

Why the wrapper is named EGINetStation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The upstream ``egi-pynetstation`` package exposes its low-level ECI client as
``NetStation``::

   from egi_pynetstation import NetStation

This plugin exposes ``EGINetStation`` so code can distinguish the
PsychoPy-compatible wrapper from that upstream class. The ``EGI`` prefix does
not indicate different hardware: the wrapper controls the same EGI/Magstim
NetStation system while adding PsychoPy ``BaseDevice`` integration, Builder
support, logging, drift configuration, and safe cleanup.

Option 2: PsychoPy Device Manager
---------------------------------

Use Device Manager when the experiment already keeps its hardware in
PsychoPy's shared device registry. ``deviceName`` is the lookup key for later
calls to ``DeviceManager.getDevice("netstation")``:

.. code-block:: python

   from psychopy.hardware import DeviceManager

   ns = DeviceManager.addDevice(
       deviceClass="psychopy_egi_pynetstation.hardware.netstation.EGINetStation",
       deviceName="netstation",
       ip="10.10.10.42",
       ntpIP="10.10.10.51",
       port=55513,
   )

Common recording workflow
-------------------------

After either construction option, use the same direct method calls. Keep
cleanup in ``finally`` so normal completion and handled early exits both stop
recording, flush asynchronous events, and disconnect:

.. code-block:: python

   try:
       ns.connect()
       ns.beginRecording()

       win.callOnFlip(
           ns.sendEvent,
           eventType="stim",  # exactly four characters
           label="face",
           duration=0.1,
       )
       win.flip()
   finally:
       ns.close()

For a non-visual event, call ``ns.sendEvent(...)`` directly instead of using
``win.callOnFlip``. For visual stimuli, the flip callback timestamps the marker
to the flip that actually presents the stimulus.

``sendEvent`` is asynchronous by default. ``endRecording`` and ``disconnect``
flush queued events, and ``close`` safely performs both operations when needed.
A transmission failure cannot raise back into the original flip callback;
``close`` reports failures through PsychoPy's logger, and ``eventErrors()``
provides the collected exceptions for programmatic inspection.

Hardware wrapper
----------------

.. automodule:: psychopy_egi_pynetstation.hardware.netstation
   :members:
   :undoc-members:
   :show-inheritance:

Display-timing helpers
----------------------

.. automodule:: psychopy_egi_pynetstation.timing
   :members:
