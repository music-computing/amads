Design Considerations
=====================

This document is an early design document, probably supplanted by
other documentation, but reviewed and converted to Markdown on
10 Jan 2026, so it should be accurate.

Terminology and Structure
-------------------------

- `onset` refers to the start time of a note or other event.

- `offset` refers to the ending time of a note or other event.

- `duration` refers to `offset - onset`

- Scores are hierarchical, but all nodes and leaves represent
  `onset` directly in absolute beat or time (not relative to the
  onset time of the parent). The end time is called `offset` and is
  computed as onset + duration.  (Note that in contexts outside of
  AMADS, "offset" is a synonym for "displacement," which is
  essentially a "delta" or "difference," so be careful not to be
  confused: "onset" is the beginning, "offset" is the ending!)

The use of absolute onset times makes it relatively expensive to shift
an object in time. E.g. to move a measure to a later time, you must
shift not only the `onset` of the `Measure` but also all of the
`Note`s and other objects in the `Measure`. However, the most
common reason to use a `Measure` or some other object at another
time is to reuse the object in a different context, e.g. to copy a
measure from one part to another part. Since all member objects have a
reference to their parent, the copy must be a deep copy of the entire
subtree. Given the cost of the deep copy, the cost of recomputing the
`onset`s is negligible. In addition, using an absolute `onset`
simplifies a lot of code and makes access to the `onset` more
efficient.

The music representation hierarchy is constrained to match intuitive
ideas about music structure. The levels of hierarchy are `Score`,
`Part`, `Staff`, `Measure`, `Chord`, `Note`, and
`Rest`. Often, this is overkill for the task at hand, so we support
a "flat" representation which is basically a list of `Note`
objects. More on this in the next section.

The edge or leaf-nodes of the representation hierarchy include
`Note` and `Rest` classes. All of these inherit from an abstract
superclass called Event, which is basically just `onset`,
`duration` and `parent` attributes. The `Note` subclass adds
attributes for `pitch`, `dynamic`, `tie`, etc.

Inner levels of hierarchy are represented by subclasses of
`EventGroup`, which is in turn an `Event` with an added attribute
named `content`, a list of children. E.g. a `Measure` is an
`EventGroup`. You might expect the duration of an `EventGroup` to
be implied by the content, but especially if Rests are removed, a
`Measure` has a duration that is independent of the content. An
`EventGroup` duration is mainly relevant of you want to append nodes
sequentially: The duration gives you the offset time, which becomes
the onset time of the next appended element.

Pitch is structured and includes a representation of accidentals, so
AMADS can disambiguate between Bb and A#, for example.

Time
----

Time is normally measured in quarters, regardless of the meter. So a
measure in 4/16 time has a duration of 1 (not 4). Scores have a tempo
and information corresponding to a Standard MIDI File tempo track, so
AMADS can convert from quarters to seconds or seconds to quarters.

To work in seconds, it is most efficient to convert the entire score
to seconds, meaning that every `onset` and `duration` attribute is
converted in one pass through the score. Since the entire score stores
time in one unit or the other, there are no separate attributes such as
`offset_seconds` or `duration_seconds`, and computed values such as
`offset` run identical computations whether the units are beats or
seconds, so they return values in the same units as are stored in the
score.

### Conversion to Seconds

Conversion to seconds is done in-place. This violates the immutable
Score design (see next section) but note that if you convert back to
beats, you can restore the original score, so changes are not
*necessarily* visible even when scores are shared. Conversion involves
using the score `TimeMap` to map between quarters and seconds. The
`TimeMap` is stored as an array of breakpoints, so a lookup involves
a search, but since most accesses are in time order, it is possible to
cache the location of the previous lookup in case the next one is
nearby. Thus, we can expect to make a single pass through the
`TimeMap` to convert each `Staff` and its children.


Immutable Scores
----------------

In general, music structures in AMADS are immutable. This means that
once you read or construct a score, you can extract data and reformat
the data without side-effects from analysis functions. For example,
given a piano score, you can extract the top staff into a new
score. This will *not* delete the bottom staff, so you can still
extract the bottom staff into another score. Similarly, if you merge
all tied notes in a score, any references you had to notes before the
merge will remain unaffected because the notes will be merged in a
copy.

Elements of the Score hierarchy have access to their parent, so
parents cannot generally share sub-trees. E.g. to extract the flute
Part from a complete Score, AMADS cannot simply construct a new Score
that contains just the flute Part, because the original flute Part's
parent is the original Score. Instead, the entire flute Part (but no
other Parts) must be deep-copied to assign new parents to elements of
the copy.

It would be prohibitively expensive to rule out all modifications to
Scores, e.g. transposing 100 notes should not make 100 copies of the
original score, making one change at a time. The rule is that once you
copy a score, you can make any number of modifications as long as
there are no shared references to the score or score elements. Thus,
scores are not *observably* mutable from the "outside" of
computations. AMADS transformations such as `flatten` or
`merge_tied_notes` generally make a single copy even though there
are many changes.

Another case is that some analysis algorithms need to report results
on a per-note basis, e.g. assigning an entropy value to each note. In
these cases, the analysis algorithm can create and set an
analysis-specific attribute, e.g. `entropy`, on each
note. Essentially, algorithms are allowed to *annotate* scores by
adding new events and attributes, as long as they do not change
existing attributes or insert or delete Notes, Rests, Chords or other
event types understood by AMADS.

In keeping with Python best practices, we do not use Python's
ability to add attributes to objects dynamically. Instead, there
is one attribute, `info`, on every `Event` that serves as a dictionary
for additional information that does not have a place in the
declared attributes. We consider `info` to be mutable, so analysis
algorithms and their users should be careful to avoid overwriting
information there.


Basic Representation and Simplifications
----------------------------------------

The “standard” score has parts representing instrumental parts. Each
part has 1 or more staves (e.g. a piano part would ordinarily have 2
staves [“staves” is the plural of “staff”, but documentation often
uses “staffs” in the sense of “multiple instances of the Staff
class.”]), each staff has measures, and measures have notes and chords
which have notes. Notes can be tied, so a single “logical” note can be
represented (as in standard notation) by multiple notes tied
together. This is basically because notes do not fit within the
hierarchy imposed by measures and beats. When a note crosses a measure
boundary, and sometimes when it crosses a beat boundary, at least in
conventional notation, it must be split across these boundaries and
the original note is indicated by ties between the fragments.

All this hierarchy can get in the way, so we allow various
simplifications:

- Tied notes can be replaced by single notes, with durations that may
  extend beyond a measure boundary (`merge_tied_notes()` method)

- Rests can be removed (`remove_rests()` method)

- Staves within each part can be collapsed to a single staff
  (currently, no method does just this)

- Chords can be removed, moving notes “up” into measures
  (`expand_chords()` method)

- Staves, measures and chords can be removed and all "leaf" notes
  moved directly into parts (`flatten()` method, which additionally
  removes ties as in `merge_tied_notes()` since there are no more
  explicit measures)

- Multiple parts can be combined into a single part (`merge_part()`
  method, but this also does `flatten()` which implies
  `merge_tied_notes()`)

So there are lots of variations all having to do with removing
different hierarchies. We considered a hierarchy of representations,
each with additional notation details or hierarchy, but this seems
too complicated and while it might be appropriate for certain kinds
of analysis, the intermediate levels of simplification do not
correspond to any familiar notation and so they are not intuitive.

In conclusion, the main thing users should think about is measure
structure vs. “flat” note lists, so we have two categories for scores:
*full* and *flat*. Within these types, we can have checks for
the more subtle differences and operations to remove structure:

### Full Scores

`.has_rests()`
    The Score or Part or Staff or Measure has one or more Rest objects.

`.remove_rests()`
    Construct a Score or Part or Staff or Measure without any
    Rests. Note that removing rests does not change the timing of
    notes or other objects since each Events has a delta time relative
    to the parent (as opposed to music notation where a note begins
    after a previous note or rest).

`.has_chords()`
    The Score or Part or Staff or Measure has one or more Chord objects.

`.expand_chords()`
    Convert a Score, Part, Staff or Measure to one without chords
    (chord notes become ordinary notes within the parent).

`.has_ties()`
    The Score, Part, Staff or Measure has one or more tied notes.

`.merge_tied_notes()`
    Convert the Score, Part, Staff or Measure to one without
    ties. Although not required, we expect ties to break notes where
    they cross measure boundaries.  After `.merge_tied_notes()`,
    notes may cross one or more measure boundaries.

`.remove_measures()`
    The `.remove_measures()` method "lifts" notes into the Staff
    level, preserving each Staff. This is neither a Full Score
    nor a Flat Score, but might be useful in processing each Staff
    separately. Note that tied notes can cross staves.
    `remove_measures()` merges ties to eliminate staff-crossings.
    For example if (staff 1, note 1) ties to (staff 2, note 2), then
    note 2 will be removed from staff 2 (and the duration of note 1
    will be adjusted).

`.flatten()`
    Convert a full score into a flat score. Parts are preserved or
    collapsed based on an optional parameter. Tied notes are always
    merged because we assume ties are not useful in this
    context. Non-Note events are not retained in Part(s) because they
    might only be relevant within the hierarchy of a measured
    score. However, non-Note events can be inserted into a flat score.

`.collapse_parts()`
    Merge the notes of selected Parts and Staffs into a flat score
    with one Part. When called with no part or staff selection, all
    notes are combined this is equivalent to
    `.flatten(collapse=True)`.

### Flat Scores

`.is_flat()`
    Test if this is a flat score. A flat score has a strict hierarchy
    described by: Score-Part-Note. There are no tied notes. Also,
    there are no Staff, Measure, Rest or Chord objects, but there may
    be other subclasses of Events at any level.

`.is_flat_and_collapsed()`
    Test if this is a flat score with one and only one Part.

`.part_count()`
    Returns number of parts

### Other Scores

Scores which are neither Full nor Flat are at least possible
to construct. E.g. a Score-Part-Note hierarchy with tied notes
or a Score with a mix of measured and flattened Parts. Developers
should consider that valid Full Scores could have Chord objects
with zero or one Notes.

Ideally, algorithms should detect violations in assumptions and report
them as errors: We do not want users to call functions with an
intuitive idea of what they *should* do, only to get some
non-intuitive result that the user does not notice. It's better to
raise an error to say “you can't do this, or I don't support it” than
to silently return something possibly wrong.

The `.is_well_formed()` and `.is_well_formed_full_score()` methods
can check for conformance to the standard forms.

## Distributions and Histograms

The Distribution class models statistical distributions or
histograms. Attributes describe the data with enough detail to produce
reasonably labeled plots, so by returning a Distribution object
rather than simply a vector, the user can call `.plot()` without
even knowing the proper axes and labels.

Distributions are often built with a Histogram object to do
calculations, but the Histogram class can be used independently
of Distributions, and neither is a subclass of the other.
