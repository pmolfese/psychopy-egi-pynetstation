PsychoPy EGI NetStation
=======================

``psychopy-egi-pynetstation`` adds EGI/Magstim NetStation recording control
and event markers to PsychoPy Builder and Python experiments. It communicates
with NetStation's ECI server through ``egi-pynetstation``.

.. image:: ../images/1-components.png
   :alt: EGI Connect, Disconnect, Send Event, Start Recording, and Stop Recording in PsychoPy Builder's EEG component panel
   :align: center
   :width: 360px

Use the plugin through five Builder Components under **I/O > EEG**, through a
direct Python ``EGINetStation`` instance, or through PsychoPy's Device Manager.
Builder network settings live in **EGI Connect**; no Device Manager
configuration or amplifier auto-discovery is required for that interface.

Automatic clock-drift correction is enabled by default. After the initial NTP
synchronization, the plugin samples the amplifier clock on a background thread
and corrects event timestamps on the client side as the clocks drift apart. No
extra Builder Component or Coder call is required; advanced users can disable
or configure the behavior through EGI Connect or the Python API.

.. important::

   Version |release| is an initial public-release candidate. The wrapper and
   generated Builder code are tested automatically, but end-to-end validation
   with physical or simulated NetStation hardware is still in progress.
   Validate the complete workflow in your lab before collecting production
   data.

Start here
----------

* :doc:`getting-started` — install the plugin and build a minimal experiment.
* :doc:`builder-components` — understand every option shown in the GUI.
* :doc:`timing` — choose flip synchronization and understand display timing.
* :doc:`python-api` — use the plugin from PsychoPy Coder or another Python experiment.
* :doc:`troubleshooting` — diagnose common setup and runtime problems.

.. toctree::
   :maxdepth: 2
   :caption: User guide
   :hidden:

   getting-started
   builder-components
   timing
   python-api
   troubleshooting

.. toctree::
   :maxdepth: 1
   :caption: Project
   :hidden:

   contributing
