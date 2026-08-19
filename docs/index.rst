PsychoPy EGI NetStation
=======================

``psychopy-egi-pynetstation`` adds EGI/Magstim NetStation recording control
and event markers to PsychoPy Builder and Python experiments. It communicates
with NetStation's ECI server through ``egi-pynetstation``.

.. image:: ../images/1-components.png
   :alt: EGI Connect, Disconnect, Send Event, Start Recording, and Stop Recording in PsychoPy Builder's EEG component panel
   :align: center
   :width: 360px

The plugin provides five Builder Components under **I/O > EEG**. Network
settings live in **EGI Connect**; no PsychoPy Device Manager configuration or
amplifier auto-discovery is required.

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
* :doc:`python-api` — control NetStation from a Python experiment.
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
