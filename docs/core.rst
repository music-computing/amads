
.. _core-sec:

Core Data Structures
====================

Quick overview: The basic hierarchy of a score is shown here.
Each level of this hierarchy can contain 0
or more instances of the next level. There are two representations: a
"full" score retains most of the structure of Western classical
notation, while a "flattened" score is a more abstracted
representation emphasizing notes.

A "full" score looks like this:

    | **Score** - one per musical work or movement
    |     **Part** - one per instrument 
    |         **Staff** - usually 1, but e.g. 2 for grand staff
    |             **Measure** - one for each measure. Each measure
      can contain multiple instances of the following:
    |                 **Note**
    |                 **Rest**
    |                 **Chord**
    |                     **Note** - one for each note of the chord
    |                 **KeySignature**
    |                 **TimeSignature**
    |                 **Clef**

A "flattened" score looks like this:

    | **Score** - one per musical work or movement
    |     **Part** - one per instrument 
    |         **Note** - no other instances allowed, no ties

Well-Formed Scores
~~~~~~~~~~~~~~~~~~

Score structure is not enforced (it is up to the developer), but AMADS functions will return well-formed scores in either of the "full" score or the "flattened" score forms shown above.

A well-formed score will have events belonging to a parent (EventGroup) in time order.

Rests objects are created when scores are read from MusicXML, but MIDI
has no representation for rests and the MIDI file reader does not
insert Rest objects. Generally, you should ignore Rests since Notes
all have ``onset``\s, so Rests are not needed for timing.


Tempo, Time, Duration
---------------------

Time is usually measured in "quarters". ("Beat" is avioded since it is
often ambiguous -- how many beats per measure are in 6/8 time?)  Time
can also be measured in real-time units of seconds.

Tempo is indicated at the score level as a single mapping between
seconds and quarters.

You can convert every time and duration in an entire score from
quarters to seconds (and vice versa), allowing you to work in musical
time or real time. (See
:py:meth:`~amads.core.basics.Score.convert_to_seconds()` or
:py:meth:`~amads.core.basics.Score.convert_to_quarters()`. 


Events and EventGroups
----------------------

To implement this hierarchical representation, we have *one* superclass, which is :py:class:`~amads.core.basics.Event`. Every Event has the following attributes:

.. container:: attributes

   :onset: (float) The time of the event
   :duration: (float) The duration (in beats or seconds) of the event
   :parent: (EventGroup) The object containing this event
   :info: a dictionary with (optional) additional information

Anything that can be a ``parent`` is an :py:class:`~amads.core.basics.EventGroup`. EventGroups including Part, Staff, Measure and Chord are also children, so you would expect them to be Events. There is no conflict because EventGroup *inherits from* Event.  Everything is an Event! But not every Event is an EventGroup.

Onset Times
-----------

Onset times (as either quarters or seconds) are *zero-based* and *absolute*. Two measures of quarter notes in 4/4 time will have ``onsets`` of 0, 1, 2, 3, 4, 5, 6, 7. Note that the downbeat is *not* 1, and the first beat of the second measure is 4, not 0 or 1.

Finally, ``onset`` can be None during the construction of a Score. If the ``onset`` is None and a Note (Event) is appended to the Events in a Measure (EventGroup), the ``onset`` of the Note is set so that the Events are sequential in time. This can be a convenience when writing expressions like ``Measure(Note(), Note(), Rest(), Note())``, but *we recommend that you always specify onset times*.


The Note Class
--------------

The most important class is :py:class:`~amads.core.basics.Note`. In addition to `onset`, `duration` and `parent`, inherited from Event, a Note has

.. container:: attributes

   :pitch: (Pitch) A pitch object (see below)
   :dynamic: (optional int or str) dynamic (loudness) level
   :lyric: (optional str) lyric text
   :tie: (optional Note) the Note this Note is tied to, if any

Pitches
-------

Pitches are complex enough to get their own class (an integer will not do). The pitch class has these attributes:

.. container:: attributes

   :key_num: (float) MIDI-like key number, e.g. C4 = 60
   :alt: (float) Alteration, e.g. one flat = -1

Notice that you can always ignore ``alt`` and just use ``key_num``, but if you care about note spelling, you will need ``alt``.

Notice also that both ``key_num`` and ``alt`` are floats, so you can express quarter tones (a quarter tone above C4 is represented by 60.5), and the ``alt`` would be 0.5 (a quarter tone sharp).

The Pitch class has a wealth of properties to obtain the name as a string, the octave, pitch class, and others.


Immutable Scores (Mostly)
-------------------------

In general, AMADS Scores are immutable, which means you cannot (or should not) change them. When you need changes (consider simple operations like time-stretching a score or transposing or removing all but one instrument), AMADS almost always returns a *copy*, leaving the original intact. The goal is to avoid surprising side effects when the same score is passed through different operations and analyses.

There are important exceptions. Some examples:

- :py:meth:`~amads.core.basics.Score.convert_to_seconds()` or :py:meth:`~amads.core.basics.Score.convert_to_quarters()` change the score (but either operation can be undone by calling the other),

- it is permissible to "annotate" a score by adding new information, e.g., setting new attributes to the Events' ``info``.

- during construction, when there is only one reference to a Score, it is normal to modify the score by inserting new events.

You should **never** modify a Pitch. Always construct a new one, because when Notes are copied, the new Note *shares* the original Note's Pitch object. Assigning to ``pitch.key_num`` might change the ``pitch`` of many other notes.

Accessing and Processing Scores
-------------------------------

If you access notes directly, be aware that notes can be tied: Not every Note object represents a new performed tone. Also, Measures can contain Chord events that contain Notes, so Notes can exist at two levels of the hierarchy. Because of these and other complications, it is recommended that you use Score methods to extract the information you need rather than using your own code to traverse a Score.

To process all notes in time order, call the Score method :py:meth:`~amads.core.basics.Score.get_sorted_notes`, which returns a flat list of all notes, ordered by onset time, with ties merged.
 
If you need notes from a particular staff or part, use :py:meth:`~amads.core.basics.Score.collapse_parts` to obtain a score with only the desired information, and then apply :py:meth:`~amads.core.basics.Score.get_sorted_notes` to get the Notes.
