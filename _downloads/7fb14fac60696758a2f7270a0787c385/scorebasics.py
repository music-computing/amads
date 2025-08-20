"""
Score Creation and Manipulation Example
=======================================

This example demonstrates ways to create and populate Score objects
using the AMADS library.
"""

from amads.core.basics import Measure, Note, Part, Rest, Score, Staff
from amads.core.timemap import TimeMap

"""
Let's begin by creating the simplest kind of score:
a flattened score with a single part. We'll use the
"declarative" style using nested constructors. Since
Note onsets are not specified, Notes will be arranged
sequentially.

The score will be C-G-C with 2 quarters followed by a half
note. (The default duration of a Note is 1 quarter == 1)
"""

score = Score(Part(Note(pitch="C5"), Note(pitch="G4"), Note(pitch="C5", duration=2)))

score.show()

"""
The result of pack is to place the notes consecutively, but what
if we want something different? Here is the same score, but the
first two notes are eighth notes followed by eighth rests.
"""
score = Score(
    Part(
        Note(pitch="C5", duration=0.5),
        Rest(duration=0.5),
        Note(pitch="G4", duration=0.5),
        Rest(duration=0.5),
        Note(pitch="C5", duration=2),
    )
)
score.show()

"""
A well-formed flattened score does not have Rest objects, so we need
a different approach to create a proper flattened score. To make a
flattened score (no Rests) but with non-consecutive notes, onsets
are made explicit.
"""
score = Score(
    Part(
        Note(pitch="C5", duration=0.5),
        Note(onset=1, pitch="G4", duration=0.5),
        Note(onset=2, pitch="C5", duration=2.0),
    )
)
score.show()

"""
The same technique can be used to create overlapping notes. Here is
a tritone resolution: F and B to E and C in two half-note chords.
"""
score = Score(
    Part(
        Note(onset=0, pitch="F4", duration=2),
        Note(onset=0, pitch="B4", duration=2),
        Note(onset=2, pitch="E4", duration=2),
        Note(onset=2, pitch="C5", duration=2),
    )
)
score.show()

"""
Taking a more computational approach, we can compute a score
rather than writing out each object separately. Generally,
the declarative style does not work well for computed scores,
so we will build the score from the bottom up. Here is a
chromatic scale in quarter notes, starting at C4 and ending
on a whole note at C5.
"""
part = Part()
for i in range(12):  # another octave for a whole note
    note = Note(parent=part, onset=i, pitch=60 + i)
# create a whole note at the end of the last note:
note = Note(parent=part, onset=note.offset, pitch="C5", duration=4)
# not strictly necessary, but since part.duration is not updated
# when content is added, we set it explicitly here:
part.duration = note.offset
score = Score(part)  # put the part into a score
score.show()

"""
Now, create a full score with Part, Staff, and Measure objects
using the declarative approach.
"""
score = Score(
    Part(
        Staff(
            Measure(
                Note(pitch="C5"),
                Note(pitch="D4"),
                Note(pitch="E4", duration=2),
                pack=True,
            )
        )
    )
)
score.show()

"""
Here is a slightly more complex example with multiple staves and parts.
"""

score = Score(
    Part(
        Staff(
            Measure(Note(pitch="C5", duration=2), Note(pitch="B4", duration=2)),
            Measure(Note(pitch="C5", duration=4)),
        ),
        instrument="Flute",
    ),
    Part(
        Staff(
            Measure(Note(pitch="E4", duration=2), Note(pitch="F4", duration=2)),
            Measure(Note(pitch="E4", duration=4)),
        ),
        Staff(
            Measure(Note(pitch="C4", duration=2), Note(pitch="G3", duration=2)),
            Measure(Note(pitch="C3", duration=4)),
        ),
        instrument="Piano",
    ),
)

score.show()

"""
Given a full score, we often want to extract a selected set of notes.
Here are just the flute notes from the previous score.
"""

# collapse_parts both flattens and selects notes:
flute_score = score.collapse_parts(part="Flute")
print("Flute notes:")
for note in flute_score.find_all(Note):
    note.show(indent=4)  # prints all notes in the flute part

"""
Rather than flute_score.find_all(Note), you can also write
flute_score.list_all(Note) which returns a list rather than
a generator. Since the score is already flattened by collapse_parts,
you can also access the notes directly using
flute_score.content[0].content, which retrieves the first part's content.
"""

"""
When accessing notes in a full score with multiple parts, find_all()
and list_all() will return all notes in the order of part, staff and
measure, not in time order. You can get notes in time order using
get_sorted_notes(). Here are short programs to list all notes in
both part order and time order.
"""

print("Full score notes in part order:")
for note in score.find_all(Note):
    note.show(indent=4)
print("Full score notes in time order:")
for note in score.get_sorted_notes():
    note.show(indent=4)

"""
Sometimes, you want to use time in seconds rather than in quarters.
You can convert a score to seconds easily. This is an *in-place*
change, modifying the score object. You can revert to beats as shown.
"""
print("Is the score in quarters?", score.units_are_quarters)
score.convert_to_seconds()
print("Is the score now in seconds?", score.units_are_seconds)
print("Full score notes in time order (seconds):")
for note in score.get_sorted_notes():
    note.show(indent=4)
# revert to quarters
score.convert_to_quarters()
print("Is the score back in quarters?", score.units_are_quarters)

"""
You can change the tempo at any time and as often as you like.
As in MIDI files, there are no continuous tempo changes, but you
can get the effect by changing the tempo at every quarter or even
finer division.

Tempo changes do not affect times in the score, so if units are
quarters, a faster tempo will make the notes shorter in seconds,
but if units are seconds, the notes will remain the same length
in seconds, so their durations in quarters will be increased.

This example doubles the tempo of the score. When we convert to
seconds, the notes will be half as long in seconds.
"""

# change the tempo
tempo = score.time_map.beat_to_tempo(0)  # initial tempo
print("Initial tempo:", tempo)
score.time_map = TimeMap(tempo * 2)  # double the tempo
print("New tempo:", score.time_map.beat_to_tempo(0))
# convert to seconds
score.convert_to_seconds()
print("Full score notes in time order (seconds, after tempo change):")
for note in score.get_sorted_notes():
    note.show(indent=4)
# revert to quarters
score.convert_to_quarters()
