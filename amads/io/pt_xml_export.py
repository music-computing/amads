from typing import Optional, cast

from partitura import save_performance_midi
from partitura.score import GenericNote as ptGenericNote
from partitura.score import Measure as ptMeasure
from partitura.score import Note as ptNote
from partitura.score import Part as ptPart
from partitura.score import Score as ptScore
from partitura.score import Staff as ptStaff

from amads.core.basics import EventGroup, Measure, Note, Part, Score, Staff

DIVS = 600  # divisions per quarter note for Partitura MIDI export
# 600 corresponds to 1 ms at 100 bpm


def add_event_to_part(
    event, pt_part: ptPart, staff: Optional[int], id: int
) -> int:
    """Add an AMADS event to a Partitura part.

    This is a recursive function that handles different event types.
    Partitura requires Staff objects to have IDs and Notes to have
    Staff ID's (if there are multiple staves), so we pass in the
    staff ID when iterating through a Staff's content, and to
    support assigning unique IDs to new Staffs, we pass in a
    "suggested" object ID; if it is used, we return the ID + 1
    to be passed to the next Staff in the (Part's) content.

    Also, Partitura numbers measures starting at 1, but AMADS
    allows measures without numbers and allows strings as measure
    numbers; we assign our own count to measures and assign
    AMADS measure numbers to the Partitura Measure name attribute.
    """
    pt_group = None
    if isinstance(event, Staff):  # must be full score
        pt_group = ptStaff(number=id)
        staff = id
        id += 1  # so we can return and id for the next Staff
    elif isinstance(event, Measure):
        event = cast(Measure, event)
        name = None if event.number is None else str(event.number)
        pt_group = ptMeasure(number=id, name=name)
    if isinstance(event, EventGroup):  # e.g. Part, Staff, Measure
        if pt_group is not None:
            pt_part.add(
                pt_group, round(event.onset) * DIVS, round(event.offset) * DIVS
            )
        subid = 1
        for subevent in event.content:
            subid = add_event_to_part(subevent, pt_part, staff, subid)
    elif isinstance(event, Note):
        event = cast(Note, event)
        if event.pitch is None:
            pt_note = ptGenericNote(staff=staff)
        else:
            pt_note = ptNote(
                step=event.step,
                octave=event.octave,
                alter=event.pitch.alt,
                staff=staff,
            )  # type: ignore
            assert pt_note.midi_pitch == event.key_num, (
                "internal error in pitch"
                " conversion; maybe octave confusion for something like B#3?"
            )
        pt_part.add(
            pt_note, round(event.onset) * DIVS, round(event.offset) * DIVS
        )
    return id


def score_to_partitura(
    score: Score,
    show: bool = False,
) -> ptScore:
    """Convert an AMADS Score to a Partitura score."""
    parts = []
    previous_part_number = 0
    for part in score.find_all(Part):
        part = cast(Part, part)
        part_number = part.number
        if part_number is None:
            previous_part_number += 1
            part_number = previous_part_number
        else:
            part_number = int(part_number)
            previous_part_number = max(previous_part_number, part_number)
        pt_part = ptPart(id=part_number)
        parts.append(pt_part)
        events = part.content
        for event in events:
            add_event_to_part(event, pt_part, staff=None, id=1)
    pt_score = ptScore(partlist=parts)
    if show:
        print("Partitura score structure: class is", pt_score.__class__)
        print("------- here are the parts -------")
        for ptpart in pt_score.parts:
            print(ptpart.__class__)
            print(ptpart.pretty())
    return pt_score


def partitura_midi_export(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Use Partitura to export a Score to a Standard MIDI file.

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the MIDI data.
    show : bool, optional
        If True, print the Partitura score structure for debugging.
    """
    pt_score = score_to_partitura(score, show)
    save_performance_midi(pt_score.parts, filename)
