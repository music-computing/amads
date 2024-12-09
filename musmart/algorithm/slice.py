"""

Author: Peter Harrison
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Union

from ..core.basics import Note, Score
from ..utils import float_range


@dataclass
class Timepoint:
    time: float
    note_ons: list[Note] = field(default_factory=list)
    note_offs: list[Note] = field(default_factory=list)
    sounding_notes: set[Note] = field(default_factory=set)

    @property
    def last_note_end(self):
        return max(n.offset + n.dur for n in self.sounding_notes)


def get_timepoints(notes: List[Note], time_n_digits: Optional[int] = None) -> List[Timepoint]:
    note_ons = defaultdict(list)
    note_offs = defaultdict(list)

    for note in notes:
        note_on = note.offset
        note_off = note.offset + note.dur

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

        timepoints.append(Timepoint(
            time=time,
            note_ons=note_ons[time],
            note_offs=note_offs[time],
            sounding_notes=sorted(list(sounding_notes), key=lambda n: n.keynum),
        ))

    return timepoints


class Slice:
    def __init__(
            self,
            notes: List[Note],
            original_notes: List[Note],
            start: float,
            end: float,
        ):
        self.notes = notes
        self.original_notes = original_notes
        self.start = start
        self.end = end

    def __iter__(self):
        return iter(self.notes)

    def __len__(self):
        return len(self.notes)

    @property
    def duration(self):
        return self.end - self.start

    @property
    def is_empty(self):
        return len(self.notes) == 0


def salami_slice(
        passage: Union[Score, Iterable[Note]],
        remove_duplicated_pitches: bool = True,
        include_empty_slices: bool = False,
        include_note_end_slices: bool = True,
        min_slice_duration: float = 0.01,
) -> List[Slice]:
    if isinstance(passage, Score):
        notes = passage.flatten(collapse=True).find_all(Note)
    else:
        notes = passage

    timepoints = get_timepoints(notes)
    slices = []

    for i, timepoint in enumerate(timepoints):
        if (
            len(timepoint.note_ons) > 0
            or (include_note_end_slices and len(timepoint.note_offs) > 0)
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

            slice_start = timepoint.time

            if next_timepoint is None:
                if len(timepoint.sounding_notes) == 0:
                    continue
                else:
                    slice_end = timepoint.last_note_end
            else:
                slice_end = next_timepoint.time

            slice_duration = slice_end - slice_start

            if slice_duration < min_slice_duration:
                continue

            pitches = [note.pitch for note in timepoint.sounding_notes]
            if remove_duplicated_pitches:
                pitches = sorted(set(pitches))

            notes = [
                Note(
                    offset=slice_start,
                    dur=slice_duration,
                    pitch=pitch,
                )
                for pitch in pitches
            ]

            slices.append(Slice(
                notes=notes,
                original_notes=timepoint.sounding_notes,
                start=slice_start,
                end=slice_end,
            ))

    return slices


class Window(Slice):
    def __init__(
            self,
            time: float,
            size: float,
            align: str,
            candidate_notes: Iterable[Note],
            skip: int = 0,
    ):
        # TODO: document that candidate_notes must be ordered by offset and pitch

        match align:
            case "left":
                start = time
            case "center":
                start = time - size / 2
            case "right":
                start = time - size
            case _:
                raise ValueError(f"Invalid value passed to `align`: {align}")

        end = start + size

        self.time = time
        self.size = size
        self.align = align

        original_notes = []
        notes = []

        candidate_notes = list(candidate_notes)

        for i in range(skip, len(candidate_notes)):
            note = candidate_notes[i]

            if note.end_offset < start:
                # The note finished before the window started.
                # It'll definitely finish before future windows start,
                # because they'll be even later, so we can skip it then too.
                skip = i
                continue

            if note.offset > end:
                # The note starts after the window finishes.
                # All the remaining notes in candidate_notes will have even later offsets,
                # so we don't need to check them for this window.
                # They might be caught by future windows though.
                break

            original_notes.append(note)

            # We use copy instead of creating a new Note because we want to
            # preserve any other attributes that might be useful in downstream tasks.
            note = note.copy()
            note.offset = max(note.offset, start)
            note.dur = min(note.dur, end - note.offset)

            notes.append(note)

        # The next window can look at this attribute to know which candidates can be skipped.
        self.skip = skip

        super().__init__(notes=notes, original_notes=original_notes, start=start, end=end)


def window_slice(
        passage: Union[Score, Iterable[Note]],
        size: float,
        step: float = 1.0,
        align: str = "right",
        start: float = 0.0,
        end: Optional[float] = None,
        times: Optional[Iterable[float]] = None,
) -> Iterator[Window]:
    """
    Slice a score into (possibly overlapping) slices of a given size.

    Parameters
    ----------

    passage :
        The passage to slice.

    size :
        The size of each slice (time units).

    step :
        The step size to to take between slices (time units).
        For example, if step is 0.1, then a given slice will start 0.1 time units
        after the previous slice started. Note that if step is smaller than size,
        successive slices will overlap.

    align :
        Each generated window has a `time` property that points to a
        particular timepoint in the musical passage. The `align` parameter determines
        how the window is aligned to this timepoint.

        - "left" : the window starts at ``slice.time``
        - "center" : ``window.time`` corresponds to the midpoint of the window
        - "right" : the window finishes at ``slice.time``

    start :
        The desired time of the first slice (defaults to 0.0).

    end :
        If set, the windowing will stop once the end time is reached.
        Following the behaviour of Python's built-in range function,
        ``end`` is not treated inclusively, i.e. the last slice will
        not include ``end``.

    times :
        Optional iterable of times to generate slices for. If provided,
        `start` and `end` are ignored.
    """
    if isinstance(passage, Score):
        if not passage.is_flattened_and_collapsed():
            raise NotImplementedError(
                "Currently this function only supports flattened and collapsed scores. "
                "You can flatten a score using `score.flatten(collapse=True)`."
            )
        notes = passage.find_all(Note)
    else:
        notes = passage

    notes = list(notes)
    notes.sort(key=lambda n: (n.offset, n.pitch))

    if times is None:
        window_times = float_range(start, end, step)
    else:
        for par, default in [("start", 0.0), ("end", None), ("step", 1.0)]:
            provided = globals()[par]
            if provided != default:
                raise ValueError(f"`{par}` was set to {provided} but `times` was also provided")

        window_times = times

    skip = 0

    for time in window_times:
        window = Window(time, size, align, notes, skip)

        yield window

        skip = window.skip

        if skip + 1 == len(notes):
            break
