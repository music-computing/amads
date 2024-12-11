Music21
=======

https://www.music21.org/music21docs/usersGuide/

Note class
---------
* name:
  e.g. ``'F'``
* octave:
  e.g. ``5`` (ISO) 
* pitch:
  e.g. ``'F5'``, ``'B-2'``, ``'D#3'``

Maybe it would make more sense to have an alter (alteration)? Music21 uses, e.g.
``bflat.pitch.accidental.alter == -1``, so alterations are actually objects, maybe
because they have some interesting attributes like position 'left' or 'above'

Canonical note representation could be:
* ``<start, dur, pitch, lyric>``  (see Pitch and Duration below)

derived from this are:
* ``name_with_octave``
* ``pitch_class``
* ``frequency``
* ``alter_name``
* ``key_number`` (or maybe midi)
* ``unicode_name``
* ``unicode_name_with_octave``

methods include:
* ``enharmonic()``
* ``lower_enharmonic()``
* ``upper_enharmonic()``

Rests class - another class. Accessing pitch gives an exception

For convenience, Note has a lot of methods, but Note should be composed of:
* ``<start, dur, pitch, tie>``, where tie is ``'start'``, ``'stop'``, or ``'continue'`` (both)

Pitch is ``<name, octave, alter>``
and derived are:
* ``name_with_octave``
* ``pitch_class``
* ``frequency``
* ``alter_name``
* ``key_number`` (or maybe midi)
* ``unicode_name``
* ``unicode_name_with_octave``

methods include:
* ``enharmonic()``
* ``lower_enharmonic()``
* ``upper_enharmonic()``

Duration using rationals - see fractions.py
    measured in quarters
properties are:
* ``quarters``

Structure
---------
Stream is supertype for Score, Part and Measure
Streams have time (offset) and a list of components:
* ``Stream``
* ``Note``
* ``Chord``
* ``Clef``
* ``TimeSignature``
* ``Rest``?

Component offsets are relative to the parent, not global.
We can add a tempo curve that consists of breakpoints
    starting at (0,0), and map seconds to quarters
    Operations could then include: fix the tempo, e.g.
    linear mapping at some number of quarters/second;
    convert internal offsets from quarters to seconds;
    convert internal offsets from seconds to quarters.

Ties: in Music21, notes can have durations that take
    them out of the measure, OR notes can have ties.

Chord
-----
    similar to Note, but it has pitches instead of pitch
methods include:
* ``root``
* ``bass``

Tempo
-----
    not in Music21 - should add tempo curve to Stream
