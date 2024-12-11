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

   amads.algorithms.boundary
   amads.algorithms.break_it_up
   amads.algorithms.durdist1
   amads.algorithms.durdist2
   amads.algorithms.entropy
   amads.algorithms.hz2midi
   amads.algorithms.ismonophonic
   amads.algorithms.ivdirdist1
   amads.algorithms.ivdist1
   amads.algorithms.ivdist2
   amads.algorithms.ivsizedist1
   amads.algorithms.nnotes
   amads.algorithms.pcdist1
   amads.algorithms.pcdist2
   amads.algorithms.pitch_mean
   amads.algorithms.scale
   amads.algorithms.segment_gestalt
   amads.algorithms.skyline

Harmony
-------

.. autosummary::
   :toctree: _autosummary
   :caption: Harmony:

   amads.harmony.root_finding.parncutt_1988

Pitch
-----

.. autosummary::
   :toctree: _autosummary
   :caption: Pitch:

   amads.pitch.transformations

Resources
---------

.. autosummary::
   :toctree: _autosummary
   :caption: Resources:

   amads.resources.key_profiles_literature

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