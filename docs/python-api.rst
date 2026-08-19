Python API
==========

Create the device through PsychoPy's Device Manager, connect, start recording,
send events, and then stop and disconnect:

.. code-block:: python

   from psychopy.hardware import DeviceManager

   ns = DeviceManager.addDevice(
       deviceClass="psychopy_egi_pynetstation.hardware.netstation.EGINetStation",
       deviceName="netstation",
       ip="10.10.10.42",
       ntpIP="10.10.10.51",
       port=55513,
   )

   ns.connect()
   ns.beginRecording()

   win.callOnFlip(
       ns.sendEvent,
       eventType="stim",
       label="face",
       duration=0.1,
   )
   win.flip()

   ns.endRecording()
   if ns.eventErrors():
       raise RuntimeError("One or more NetStation events failed")
   ns.disconnect()

``sendEvent`` is asynchronous by default. ``endRecording`` and ``disconnect``
flush queued events, but a transmission failure cannot raise back into the
original flip callback. Always inspect ``eventErrors()`` before accepting a
run.

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
