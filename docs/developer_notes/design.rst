Design considerations
====================

Basic Representation and Simplifications
----------------------------------------

I think this is an area where the API and method names need to be
thought about carefully and possibly changed. Here are the issues that
I see...

The "standard" score has parts representing instrumental parts. Each
part has 1 or more staves (e.g. a piano part would ordinarily have 2
staves ["staves" is the plural of "staff"]), each staff has measures,
and measures have notes and chords which have notes. Notes can be
tied, so a single "logical" note can be represented (as in standard
notation) by multiple notes tied together. This is basically because
notes do not fit within the hierarchy imposed by measures and
beats. When a note crosses a measure boundary, and sometimes when it
crosses a beat boundary, it must be split across these boundaries and
the original note is indicated by ties between the fragments.

All this hierarchy can get in the way, so we allow various
simplifications:

- Tied notes can be replaced by single notes, with durations that may
  extend beyond a measure boundary (``merge_tied_notes()`` method)

- Staves within each part can be collapsed to a single staff
  (currently, no method does just this)

- Chords can be removed, moving notes "up" into measures
  (``remove_chords()`` method)

- Staves, measures and chords can be removed and all "leaf" notes
  moved directly into parts (``flatten()`` method, which additionally
  removes ties using ``merge_tied_notes()``)

- Multiple parts can be combined into a single part (``merge_part()``
  method, but this also does ``flatten()`` which also does
  ``merge_tied_notes()``)

So there are lots of variations all having to do with removing
different hierarchies. Maybe we need a "hierarchy of hierarchies", in
other words, removing one hierarchy implies removing all those below
it in the "hierarchy of hierarchies". The "hierarchy of hierarchies"
(need a more intuitive name) could be, from most abstract to most
detailed:

- Score with one part, no staves, no measures, no ties, no chords

- Score with multiple parts, no staves, no measures, no ties, no
  chords

- Score with multiple parts, staves, no measures, no ties, no chords

- Score with multiple parts, staves, measures, no ties, no chords

- Score with multiple parts, staves, measures, ties, no chords

- Score with multiple parts, staves, measures, ties, chords

This can be summarized by looking at what gets added at each level:

- Score with one part

- add multiple parts per score

- add multiple staves per part

- add measures per staff

- add ties; notes can be split the way the appear visually

- add chords; a way of grouping notes that start simultaneously

Maybe even this is too many and too flexible - do you want to take out
ties and leave measures?

Or maybe this is not flexible enough - do you want to take out
measures and leave chords?

And if restricting the number of forms that scores can take to 4 to 6
variations, can we name them? E.g. Flattened, Flat Parts, Measureless,
.... That doesn't seem like it's going to be very intuitive, e.g. who
will intuitively grasp the meaning of "measureless" vs "flattened"?

In conclusion, this is too many concepts. The main thing users should
think about is measure structure vs. "flat" note lists, so let's have
two categories for scores: measured and flattened. Within these types,
we can have properties for the more subtle differences and operations
to remove structure:

Measured Scores
~~~~~~~~~~~~~~~
``.is_measured()``
    Test if this is a measured score. A measured score has a strict 
    hierarchy described by: Score-Part-Staff-Measure-(Note or Chord-Note).
    A Staff cannot be a direct child of a Score, and a Measure cannot
    be a direct child of a Part or Score. A Chord can only be a child
    of a Measure, and a Note can only be a child of a Measure or Chord.
    (Rests and other objects are also allowed in Staff and Measure.)

``.has_chords()``
    The score has one or more chords

``.strip_chords()``
    Convert the score to one without chords (chord notes become ordinary
    notes within the staff or measure)

``.has_ties()``
    The score has one or more tied notes

``.strip_ties()``
    Convert the score to one without ties. Although not required, we
    expect ties to break notes where they cross measure boundaries.
    After ``.strip_ties()``, notes durations may indicate that they
    cross one or more measure boundaries.

``.has_measures()``
    The score has one or more measures

``.strip_measures()``
    There is NO ``.strip_measures()`` method. Such a method would
    logically leave you with Staff objects without measures, but this
    is neither a Measured Score nor a Flattened Score.

``.flatten()``
    Convert a measured score into a flattened score. Parts are preserved
    or collapsed based on an optional parameter.

Flattened Scores
~~~~~~~~~~~~~~~~
``.is_flattened()``
    Test if this is a flattened score. A flattened score has a strict
    hierarchy described by: Score-Part-Note. There are no other object
    types such as Staff, Chord, or Rest. There are no tied notes.

``.is_flattened_and_collapsed()``
    Test is this is a flattened score with all notes in a single Part.

``.part_count()``
    Returns number of parts

``.collapse_parts()``
    Merge multiple Parts into a single Part. Optional parameters allow
    for selecting only certain Parts and/or Staff objects.

Other Scores
~~~~~~~~~~~~~
Scores which are neither Measured nor Flattened are at least possible
to construct. E.g. a Score-Part-Note hierarchy with tied notes
or a Score with a mix of measured and flattened Parts. We've also 
considered "chordified" scores consisting of a sequence of Chord
objects that are possibly empty or single notes.

How all of these possibilities are handled in algorithms is not yet
determined. Ideally, algorithms should detect violations in
assumptions and report them as errors: We do not want users to call
functions with an intuitive idea of what they *should* do, only to get
some non-intuitive result that the user does not notice. It's better
to raise an error to say "you can't do this, or I don't support it"
than to silently return something possibly wrong.

Distributions
-------------

The Distribution class models statistical distributions or
histograms. Attributes describe the data with enough detail to produce
reasonably labeled plots:

``distribution_type`` - a str; one of "pitch_class", "interval",
    "pitch_class_interval", "duration", "interval_size",
    "interval_direction", "duration", "pitch_class_transition",
    "interval_transition", "duration_transition", "key_correlation"

``dimensions`` - a List of dimensions, e.g. [12] for a pitch class
    distribution or [25, 25] for an interval_transition (intervals are
    from -12 to +12 and include 0 for unison, intervals larger than
    one octave are ignored.

``name`` - a str name for this distribution that is used for plot title.

``x_categories`` - a List of str with labels for x-axis categories;
    inferred from distribution_type if needed.

``x_label`` - x-axis label; inferred from distribution_type if not
    present

``y_categories`` - a List of str with labels for y-axis categories;
    inferred from bin_centers and then distribution_type if needed

``y_label`` - y-axis label; inferred from distribution_type if not
    present

