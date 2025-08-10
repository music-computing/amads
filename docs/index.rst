AMADS Documentation
=====================

This package collects together a variety of algorithms for symbolic
music analysis, offering:
  - reference implementations of algorithms from the literature,
  - access to all from a single language (Python),
  - compatibility and interoperability through common data representations.

**The package is evolving. The API is subject to change, and many algorithms are not yet implemented, tested, or documented!**

Guide
-----

Whether you are a user or developer, basic knowledge of score
representation is essential. See :doc:`core`.

Users
~~~~~

A good place to start is to study some examples (see the navigation
sidebar). You will certainly want to read music data: See Section :ref:`io-section` below. Then, you can browse or search the list of algorithms below
to see what is available in AMADS.


Developers
~~~~~~~~~~

Various details of AMADS development are described in "Developer
notes" in the navigation sidebar. We welcome contributions. Please
contact the AMADS team and we can help with design and
interoperability issues.

For the source code, visit the `GitHub repository <https://github.com/music-computing/amads>`_.

.. We add the :hidden: directive to each toctree so that the toctree is not displayed
.. in the main page itself, but only in the sidebar.

.. toctree::
   :maxdepth: 2
   :caption: User guide:
   :hidden:

   user_guide/installation

.. _developer-notes-section:
.. toctree::
   :maxdepth: 2
   :caption: Developer notes:
   :hidden:

   developer_notes/contributing
   developer_notes/documentation
   developer_notes/design
   developer_notes/modules
   developer_notes/music21
   developer_notes/testing
   developer_notes/style
   developer_notes/making_a_release

.. toctree::
   :maxdepth: 2
   :caption: Examples:
   :hidden:

   auto_examples/index


Core
----

.. toctree::
   :maxdepth: 1

   core 
 
.. autosummary::
   :toctree: _autosummary

   amads.core.basics
   amads.core.pitch
   amads.core.timemap


General algorithms
------------------

.. autosummary::
   :toctree: _autosummary
   :caption: General algorithms:

   amads.algorithms.entropy
   amads.algorithms.nnotes
   amads.algorithms.scale
   amads.algorithms.slice.salami
   amads.algorithms.slice.window

Pitch
-----

.. autosummary::
   :toctree: _autosummary
   :caption: Pitch:


   amads.pitch.hz2midi
   amads.pitch.ismonophonic
   amads.pitch.ivdirdist1
   amads.pitch.ivdist1
   amads.pitch.ivdist2
   amads.pitch.ivsizedist1
   amads.pitch.key.profiles
   amads.pitch.pcdist1
   amads.pitch.pcdist2
   amads.pitch.pitch_mean
   amads.pitch.transformations

Time
----

.. autosummary::
   :toctree: _autosummary
   :caption: Time:

   amads.time.durdist1
   amads.time.durdist2
   amads.time.npvi
   amads.time.swing
   amads.time.tempo
   amads.time.meter.break_it_up

Harmony
-------

.. autosummary::
   :toctree: _autosummary
   :caption: Harmony:

   amads.harmony.root_finding.parncutt_1988

Melody
------

.. autosummary::
   :toctree: _autosummary
   :caption: Melody:

   amads.melody.boundary
   amads.melody.segment_gestalt
   amads.melody.contour.interpolation_contour
   amads.melody.contour.step_contour
   amads.melody.similarity.melsim

Polyphony
---------

.. autosummary::
   :toctree: _autosummary
   :caption: Polyphony:

   amads.polyphony.skyline


.. _io-section:
IO
--

.. autosummary::
   :toctree: _autosummary
   :caption: IO:

   amads.io.pianoroll
