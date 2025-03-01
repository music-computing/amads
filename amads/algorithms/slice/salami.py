"""Salami slice algorithm for segmenting musical scores.

This module implements the salami slice algorithm, which segments a musical score
into vertical slices at each note onset and offset. Each slice contains all notes
that are sounding at that point in time.

Notes
-----
The algorithm is named after the way a salami sausage is sliced into thin,
vertical segments.

Author
------
Peter Harrison
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Union

from ...core.basics import Note, Score
from .slice import Slice


@dataclass
class Timepoint:
    """A point in time with associated note events.

    Parameters
    ----------
    time : float
        The time in seconds
    note_ons : list[Note]
        Notes that start at this timepoint
    note_offs : list[Note]
        Notes that end at this timepoint
    sounding_notes : set[Note]
        All notes that are sounding at this timepoint
    """

    time: float
    note_ons: list[Note] = field(default_factory=list)
    note_offs: list[Note] = field(default_factory=list)
    sounding_notes: set[Note] = field(default_factory=set)

    @property
    def last_note_end(self):
        """Get the end time of the last note sounding at this timepoint.

        Returns
        -------
        float
            The end time
        """
        return max(n.offset for n in self.sounding_notes)

    @classmethod
    def from_notes(
        cls, notes: List[Note], time_n_digits: Optional[int] = None
    ) -> List["Timepoint"]:
        """Create a sequence of timepoints from a list of notes.

        Parameters
        ----------
        notes : List[Note]
            The notes to process
        time_n_digits : int, optional
            Number of decimal places to round times to

        Returns
        -------
        List[Timepoint]
            Sequence of timepoints with associated note events
        """
        note_ons = defaultdict(list)
        note_offs = defaultdict(list)

        for note in notes:
            note_on = note.onset
            note_off = note.offset

            if time_n_digits is not None:
                note_on = round(note_on, time_n_digits)
                note_off = round(note_off, time_n_digits)

            note_ons[note_on].append(note)
            note_offs[note_off].append(note)

        times = sorted(set(note_ons.keys()) | set(note_offs.keys()))

        timepoints = []
        sounding_notes = set()

        for time in times:
            for note in note_offs[time]:
                sounding_notes.discard(note)

            for note in note_ons[time]:
                sounding_notes.add(note)

            timepoints.append(
                Timepoint(
                    time=time,
                    note_ons=note_ons[time],
                    note_offs=note_offs[time],
                    sounding_notes=sorted(list(sounding_notes), key=lambda n: n.keynum),
                )
            )

        return timepoints


def salami_slice(
    passage: Union[Score, Iterable[Note]],
    remove_duplicated_pitches: bool = True,
    include_empty_slices: bool = False,
    include_note_end_slices: bool = True,
    min_slice_duration: float = 0.01,
) -> List[Slice]:
    """Segment a musical passage into vertical slices at note onsets and offsets ('salami slices').

    Parameters
    ----------
    passage : Score or Iterable[Note]
        The musical passage to slice
    remove_duplicated_pitches : bool, default=True
        Whether to remove duplicate pitches within each slice
    include_empty_slices : bool, default=False
        Whether to include slices with no sounding notes
    include_note_end_slices : bool, default=True
        Whether to create slices at note ends
    min_slice_duration : float, default=0.01
        Minimum duration for a slice to be included

    Returns
    -------
    List[Slice]
        The sequence of vertical slices
    """
    if isinstance(passage, Score):
        notes = passage.sorted_notes()
    else:
        notes = passage

    timepoints = Timepoint.from_notes(notes)
    slices = []

    for i, timepoint in enumerate(timepoints):
        if len(timepoint.note_ons) > 0 or (
            include_note_end_slices and len(timepoint.note_offs) > 0
        ):
            try:
                next_timepoint = timepoints[i + 1]
            except IndexError:
                next_timepoint = None

            is_last_timepoint = next_timepoint is None
            is_empty_slice = len(timepoint.sounding_notes) == 0

            if is_empty_slice:
                if not include_empty_slices:
                    continue
                if is_last_timepoint:
                    # Don't include empty slices at the end of the score
                    continue

            slice_onset = timepoint.time

            if next_timepoint is None:
                if len(timepoint.sounding_notes) == 0:
                    continue
                else:
                    slice_end = timepoint.last_note_end
            else:
                slice_end = next_timepoint.time

            slice_duration = slice_end - slice_onset

            if slice_duration < min_slice_duration:
                continue

            pitches = [note.pitch for note in timepoint.sounding_notes]
            if remove_duplicated_pitches:
                pitches = sorted(set(pitches))

            slice = Slice(
                timepoint.sounding_notes, slice_onset, slice_end - slice_onset
            )

            notes = [
                Note(
                    parent=slice,
                    delta=0,
                    duration=slice_duration,
                    pitch=pitch,
                )
                for pitch in pitches
            ]

            slices.append(slice)

    return slices
