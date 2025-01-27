Modules
=======

:Author: Roger B. Dannenberg
:Date: Sep 2024

This is an attempt to explain to myself how module naming and loading
can work for SMART. I'm not experienced with creating packages, so
this might be really basic stuff for those in the know.

First, it's good to know a package is a collection of modules. A
module is a single python script (file).

Problems
--------
- Want to control the naming (somewhat) independently of the file
  system organization.
- Want to load modules incrementally, e.g. we want to load only
  analysis algorithms that we intend to use.
- Want to load modules conditionally, such as deciding to use
  Partitura or Music21 for input/output implementation.
- Want to write test code we can run in the debugger OR from
  anywhere after installing our package with no special configuration.

What should our namespace look like?
----------------------------------

There should be one top level module name. "smart" is too generic, so
possibly amads.

Controlling naming
----------------

Within amads, we should have algorithms, e.g.

::

    amads.durdist1.durdist1(score)

is the durdist1 function. It is not (according to the file system)

::

    amads.src.algorithms.durdist1.durdist1

Putting this in ``__init__.py`` should accomplish this goal (need to
test)::

    import .src.algorithms.durdist1

Or maybe we can iterate through the algorithms directory and import
all the directories there. We need to test that this does not actually
import ``durdist1.py``, which can be imported by

::

    from amads.durdist1 import durdist1

Incremental loading
-----------------

(Need to test this) With the organization suggested above, actual
modules are loaded when imported, so the user will explicitly load
whatever is needed but nothing else.

Conditional loading
-----------------

Maybe it's better to simply load what you want. In particular, users
can write the following for Partitura IO::

    from amads.ptio import pt_midi_import

(Need to test this.)

We can also write a midi_import function that conditionally calls
pt_midi_import or m21_midi_import based on what modules are loaded.
(Need to test this.)

Running test code with the debugger
--------------------------------

In VScode, you can set PYTHONPATH to include the parent directory, but
I think we need there to be a directory actually named amads (or
whatever it's called) in order to import it that way into test
modules.
