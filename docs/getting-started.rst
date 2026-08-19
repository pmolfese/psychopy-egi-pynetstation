Getting started
===============

Requirements
------------

You need Python 3.10 or newer, PsychoPy 2026.1 or newer, and a
network-reachable NetStation host with ECI enabled. Ask the NetStation
administrator for three values:

* the IP address of the computer running NetStation;
* the ECI port, normally ``55513``; and
* the amplifier's NTP server IP address.

Install
-------

Install the package in the Python environment used by PsychoPy, then restart
PsychoPy so Builder discovers the new entry points:

.. code-block:: console

   python -m pip install psychopy-egi-pynetstation

Until the first PyPI release, install the source directly:

.. code-block:: console

   python -m pip install git+https://github.com/pmolfese/psychopy-egi-pynetstation.git

Builder quick start
-------------------

Open Builder's Components panel and expand **I/O > EEG**. The five EGI
Components should appear alongside PsychoPy's other EEG components.

.. image:: ../images/1-components.png
   :alt: Five EGI components in the PsychoPy Builder EEG section
   :align: center
   :width: 360px

Add the Components to the Flow in this order:

.. rst-class:: workflow

1. **EGI Connect** near the beginning. Enter the NetStation IP, ECI port, and
   amplifier NTP IP.
2. **EGI Start Recording** after the connection is established.
3. **EGI Send Event** wherever a marker is needed. Use a four-character event
   type such as ``stim`` or ``resp``.
4. **EGI Stop Recording** near the end.
5. **EGI Disconnect** after recording has stopped.

Keep **Device label** set to ``netstation`` on every EGI Component. This is a
plain internal name used to share the connection, not a Device Manager item.
An empty Device Manager list is expected because NetStation amplifiers cannot
be auto-discovered.

These are momentary commands: each runs once when its Component starts. A
Component's **Stop** field does not control the command and should normally be
left blank. **Event duration (s)** on EGI Send Event is different—it is the
duration stored with the NetStation event.

Preflight checklist
-------------------

Before collecting data:

* confirm that ECI is enabled and the PsychoPy computer can reach the host and
  NTP addresses;
* send a four-character test event and verify its label and duration in
  NetStation;
* stop recording and disconnect cleanly so queued asynchronous events flush;
* inspect the PsychoPy log for ``NetStation events failed to send``; and
* validate the workflow using non-production data on the actual lab network.
