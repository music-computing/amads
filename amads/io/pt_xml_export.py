from math import isclose
from typing import Optional, cast

from partitura import save_musicxml
from partitura.score import Clef as ptClef
from partitura.score import GenericNote as ptGenericNote
from partitura.score import KeySignature as ptKeySignature
from partitura.score import Measure as ptMeasure
from partitura.score import Note as ptNote
from partitura.score import Part as ptPart
from partitura.score import Rest as ptRest
from partitura.score import Score as ptScore
from partitura.score import Staff as ptStaff
from partitura.score import TimeSignature as ptTimeSignature

from amads.core.basics import (
    Clef,
    EventGroup,
    KeySignature,
    Measure,
    Note,
    Part,
    Rest,
    Score,
    Staff,
)

DIVS = 600  # divisions per quarter note for Partitura MIDI export
# 600 corresponds to 1 ms at 100 bpm

CLEF_SIGN = {
    "treble": "G",
    "bass": "F",
    "alto": "C",
    "tenor": "C",
    "percussion": "percussion",
    "treble8vb": "G",
}
CLEF_LINE = {
    "treble": 2,
    "bass": 4,
    "alto": 3,
    "tenor": 4,
    "percussion": None,
    "treble8vb": 2,
}
CLEF_OCTAVE_CHANGE = {
    "treble": None,
    "bass": None,
    "alto": None,
    "tenor": None,
    "percussion": None,
    "treble8vb": -1,
}


def is_new_key_signature(event: KeySignature, kstimes: list[float]) -> bool:
    for kstime in kstimes:
        if isclose(kstime, event.onset, abs_tol=0.001):
            return False
    kstimes.append(event.onset)
    return True


def add_event_to_part(
    event,
    pt_part: ptPart,
    kstimes: list[float],
    staff: Optional[int],
    id: int,
    ties: Optional[dict] = None,
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

    Partitura does not support per-staff key signatures, so kstimes
    is used to remember when key signatures have already been
    specified to eliminate adding duplicates.

    ties: dict mapping from AMADS Note to (partitura Note, is_tied_to)
    where is_tied_to indicates if there's an incoming tie from a previous note.
    """
    pt_group = None
    if isinstance(event, Staff):  # must be full score
        pt_group = ptStaff(number=id)
        staff = id
        id += 1  # so we can return an id for the next Staff
    # add measures, but only if no staff or in first staff:
    elif isinstance(event, Measure) and (staff is None or staff == 1):
        event = cast(Measure, event)
        name = None if event.number is None else str(event.number)
        pt_group = ptMeasure(number=id, name=name)  # no staff here
    if isinstance(event, EventGroup):  # e.g. Part, Staff, Measure
        if pt_group is not None:
            pt_part.add(
                pt_group, round(event.onset) * DIVS, round(event.offset) * DIVS
            )
        subid = 1
        for subevent in event.content:
            subid = add_event_to_part(
                subevent, pt_part, kstimes, staff, subid, ties
            )
    elif isinstance(event, Note):
        event = cast(Note, event)
        if event.pitch is None:
            pt_note = ptGenericNote(staff=staff, voice=staff)
        else:
            pt_note = ptNote(
                step=event.step,
                octave=event.octave,
                alter=event.pitch.alt,
                staff=staff,
                voice=staff,
            )  # type: ignore
            assert pt_note.midi_pitch == event.key_num, (
                "internal error in pitch"
                " conversion; maybe octave confusion for something like B#3?"
            )
        pt_part.add(
            pt_note, round(event.onset * DIVS), round(event.offset * DIVS)
        )
        # Track tied notes
        if ties is not None:
            if event.tie:  # This note is tied to event.tie
                is_tied_to = (event in ties) and ties[event][1]
                ties[event] = (pt_note, is_tied_to)
                # Mark the note this ties to as having an incoming tie
                if event.tie in ties:
                    ties[event.tie] = (ties[event.tie][0], True)
                else:
                    ties[event.tie] = (None, True)
            elif event in ties:
                # Update entry with the pt_note we just created
                ties[event] = (pt_note, ties[event][1])
    elif isinstance(event, Rest):
        event = cast(Rest, event)
        pt_rest = ptRest(staff=staff)
        pt_part.add(
            pt_rest, round(event.onset * DIVS), round(event.offset * DIVS)
        )
    elif isinstance(event, KeySignature) and is_new_key_signature(
        event, kstimes
    ):
        event = cast(KeySignature, event)
        pt_key_sig = ptKeySignature(fifths=event.key_sig, mode=None)  # no staff
        pt_part.add(pt_key_sig, round(event.onset * DIVS))
    elif isinstance(event, Clef):
        event = cast(Clef, event)
        print("Creating Partitura Clef:", event.clef, "staff:", staff)
        pt_clef = ptClef(
            staff=staff,
            sign=CLEF_SIGN[event.clef],
            line=CLEF_LINE[event.clef],
            octave_change=CLEF_OCTAVE_CHANGE[event.clef],
        )
        pt_part.add(pt_clef, round(event.onset * DIVS))
    return id


def score_to_partitura(
    score: Score,
    filename: str,
    show: bool = False,
) -> ptScore:
    """Convert an AMADS Score to a Partitura score."""
    parts = []
    previous_part_number = 0
    ties = {}  # Map from AMADS Note to (partitura Note, is_tied_to)
    # where partitura Note corresponds to the key (AMADS Note)
    for part in score.find_all(Part):
        part = cast(Part, part)
        part_number = part.number
        if part_number is None:
            previous_part_number += 1
            part_number = previous_part_number
        else:
            part_number = int(part_number)
            previous_part_number = max(previous_part_number, part_number)
        # Partitura expects part IDs as strings (used as MusicXML id attributes)
        pt_part = ptPart(
            id=str(part_number),
            part_name=part.instrument,
            quarter_duration=DIVS,
        )
        parts.append(pt_part)

        # add time signatures
        for ts in score.time_signatures:
            # partitura does not allow float/fractional beats/measure
            pt_ts = ptTimeSignature(round(ts.upper), ts.lower)
            pt_part.add(pt_ts, round(ts.time * DIVS))  # no end time?

        # add content
        id = 1  # At this level, if event is a Staff, id becomes staff number
        kstimes = []  # key signature onset times
        for event in part.content:
            id = add_event_to_part(
                event, pt_part, kstimes, staff=None, id=id, ties=ties
            )

    pt_score = ptScore(partlist=parts)

    # Fix up ties: set tie_next and tie_prev on partitura notes
    for amads_note in ties.keys():
        (pt_note, is_tied_to) = ties[amads_note]

        if pt_note is None:
            # Note was tied to but we never created its partitura note
            continue

        # Set tie_next if this AMADS note is tied to another
        if amads_note.tie and amads_note.tie in ties:
            tied_to_pt_note = ties[amads_note.tie][0]
            if tied_to_pt_note is not None:
                pt_note.tie_next = tied_to_pt_note
                tied_to_pt_note.tie_prev = pt_note

    if show:
        print(f"Partitura score structure for {filename}.")
        print(f"---- class is {pt_score.__class__}, here are the parts ----")
        for ptpart in pt_score.parts:
            print(ptpart.__class__)
            print(ptpart.pretty())
    return pt_score


def partitura_xml_export(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Save a Score to a file in musicxml format using Partitura.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the MusicXML data.
    show : bool, optional
        If True, print the partitura score structure for debugging.

    """
    ptscore = score_to_partitura(score, filename, show)
    save_musicxml(ptscore, filename)
