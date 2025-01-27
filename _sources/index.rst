amads documentation
=====================

This package collects together a variety of algorithms for symbolic music analysis.

**The package is its very early stages. The API is subject to change, and many algorithms are not yet implemented, tested, or documented!**

For the source code, visit the `GitHub repository <https://github.com/music-computing/amads>`_.

.. We add the :hidden: directive to each toctree so that the toctree is not displayed
.. in the main page itself, but only in the sidebar.

.. toctree::
   :maxdepth: 2
   :caption: User guide:
   :hidden:

   user_guide/installation

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

.. toctree::
   :maxdepth: 2
   :caption: Examples:
   :hidden:

   auto_examples/index



General algorithms
------------------

.. autosummary::
   :toctree: _autosummary
   :caption: General algorithms:

   amads.algorithms.entropy
   amads.algorithms.nnotes
   amads.algorithms.scale

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

Polyphony
---------

.. autosummary::
   :toctree: _autosummary
   :caption: Polyphony:

   amads.polyphony.skyline

Core
----

.. autosummary::
   :toctree: _autosummary
   :caption: Core:

   amads.core.basics

IO
--

.. autosummary::
   :toctree: _autosummary
   :caption: IO:

   amads.io.pianoroll