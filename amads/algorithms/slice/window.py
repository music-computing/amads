"""Sliding window algorithm.

The algorithm segments a musical score into fixed-size windows that can optionally
overlap. Each window contains all notes that are sounding within its time boundaries.

Author
------
Peter Harrison
"""

from typing import Iterable, Iterator, Optional, Union

from ...core.basics import Note, Score
from ...utils import float_range
from .slice import Slice


class Window(Slice):
    """A fixed-size window of a musical score. candidate_notes that overlap
    with this interval are copied and clipped to fit within the window.
    Notes that overlap less than 1.0e-6 duration units (whether beats or
    seconds) are mostly excluded from the window to reduce numerical issues.
    An exception is made for notes that are so short that they do not overlap
    any window by at least 1.0e-6 duration units. (This seems far-fetched,
    but zero-length notes representing grace notes are one possibility to
    consider; there may be others.)

    Additionoal details that you may not need: For very short notes, the
    window is considered closed on the left and open on the right, so
    that the window is considered to contain the note if it starts at
    the same time as the window, and a note is not in the window if it
    starts at the offset time of the window. To guarantee that
    zero-length notes are included in only one window, the offset of a
    window should be identical to the onset of the next window.
    sliding_window() takes care of this by default, but if the Window
    constructor is used directly where arithmetic with time and size is
    inexact, this may not be the case.

    Parameters
    ----------
    time : float
        The reference time for this window
    size : float
        The size of the window in time units
    align : str
        How to align the window relative to the reference time:
        - "left": window starts at reference time
        - "center": reference time is at window center
        - "right": window ends at reference time
    candidate_notes : Iterable[Note]
        Notes to consider for inclusion in this window, sorted by onset time and pitch
    skip : int, default=0
        Index to start searching from in candidate_notes. This is used to optimize
        performance when iterating through multiple windows - each window can tell
        the next window which notes it can safely skip because they end before the
        window starts.
    """

    def __init__(
        self,
        time: float,
        size: float,
        align: str,
        candidate_notes: Iterable[Note],
        skip: int = 0,
    ):
        match align:
            case "left":
                onset = time
            case "center":
                onset = time - size / 2
            case "right":
                onset = time - size
            case _:
                raise ValueError(f"Invalid value passed to `align`: {align}")

        offset = onset + size

        super().__init__(
            original_notes=[],
            onset=onset,
            duration=size,
        )

        self.time = time
        self.align = align
        # skip logic: skip is the lowest index of candidate_notes for which
        # candidate_notes[skip].offset >= onset. The next window can start
        # searching from this index.

        candidate_notes = list(candidate_notes)
        self.skip = len(candidate_notes)

        for i in range(skip, len(candidate_notes)):
            note = candidate_notes[i]

            if note.offset < onset:
                # The note finished before the window starts.
                continue
            else:  # note overlaps window, start no later than this
                # when searching for overlaps with the next winodow
                self.skip = min(self.skip, i)

            if note.onset >= offset:
                # The note starts after the window finishes.
                # All the remaining notes in candidate_notes will have even later onsets,
                # so we don't need to check them for this window.
                # They might be caught by future windows though.
                break

            # note.onset < offset, so it starts in window
            if note.offset - offset < 1.0e-6:
                # The note will not overlap with the next window.
                # Since it starts in this window, include it.
                pass
            elif offset - note.onset < 1.0e-6:
                # after clipping to window boundaries, this note
                # will be shorter than 1.0e-6, but it extends into
                # the next window, so ignore the small overlap here
                continue

            self.original_notes.append(note)

            # We use deepcopy_into instead of creating a new Note because we want to
            # preserve any other attributes that might be useful in downstream tasks.
            note = note.copy(parent=self)
            # Clip the note to fit within the window
            note.onset = max(note.onset, onset)
            note.offset = min(note.offset, offset)


def sliding_window(
    passage: Union[Score, Iterable[Note]],
    size: float,
    step: float = 1.0,
    align: str = "right",
    onset: float = 0.0,
    offset: Optional[float] = None,
    times: Optional[Iterable[float]] = None,
) -> Iterator[Window]:
    """Slice a score into (possibly overlapping) windows of a given size.

    Parameters
    ----------
    passage : Score or Iterable[Note]
        The musical passage to be windowed
    size : float
        The size (duration) of each window (time units)
    step : float, default=1.0
        The step size to take between windows (time units).
        For example, if step is 0.1, then a given slice will start 0.1 time units
        after the previous slice started. Note that if step is smaller than size,
        successive windows will overlap
    align : str, default="right"
        Each generated window has a `time` property that points to a
        particular timepoint in the musical passage. The `align` parameter determines
        how the window is aligned to this timepoint:
        - "left": the window starts at ``window.time``
        - "center": ``window.time`` corresponds to the midpoint of the window
        - "right": the window finishes at ``window.time``
    onset : float, default=0.0
        The desired time of the first window
    offset : float, optional
        If set, the windowing will stop once the offset time is reached.
        Following the behaviour of Python's built-in range function,
        ``offset`` is not treated inclusively, i.e. the last window will
        not include ``offset``. The returned iterator will stop early
        the last window is empty (i.e. contains no notes) and there are
        no more notes to process.
    times : Iterable[float], optional
        Optional iterable of times to generate windows for. If provided,
        `onset` and `offset` are ignored. The returned iterator will
        stop once all times have been processed or when an empty window
        is generated and there are no more notes to process.

    Returns
    -------
    Iterator[Window]
        Iterator over the windows
    """
    if isinstance(passage, Score):
        if not passage.is_flat_and_collapsed():
            raise NotImplementedError(
                "Currently this function only supports flattened and collapsed scores. "
                "You can flatten a score using `score.flatten(collapse=True)`."
            )
        notes = passage.find_all(Note)
    else:
        notes = passage

    notes = list(notes)
    notes.sort(key=lambda n: (n.onset, n.pitch))

    # We could rely on Window to obey `align`, but here we convert onset and
    # offset to always use "left". By using left, we can guarantee when
    # step == size that each window time computed by repeated addition of
    # step will exactly equal each previous window offset, computed as
    # onset + size in Window. This avoids any floating point rounding error
    # that could affect the windowing. (This is not a problem in the typical
    # cases where window size is 1 or a power of 2 that will be computed
    # exactly due to binary representations of floats.)
    match align:
        case "left":
            pass
        case "center":
            onset -= size / 2
            if offset is not None:
                offset -= size / 2
        case "right":
            onset -= size
            if offset is not None:
                offset -= size
        case _:
            raise ValueError(f"Invalid value passed to `align`: {align}")

    if times is None:
        window_times = float_range(onset, offset, step)
    else:
        for par, default in [("onset", 0.0), ("offset", None), ("step", 1.0)]:
            provided = globals()[par]
            if provided != default:
                raise ValueError(
                    f"`{par}` was set to {provided} but `times` was also provided"
                )

        window_times = times

    skip = 0

    for time in window_times:
        window = Window(time, size, "left", notes, skip)

        yield window

        skip = window.skip

        if skip == len(notes):
            break

    skip = 0
    if times is not None:
        for par, default in [("onset", 0.0), ("offset", None), ("step", 1.0)]:
            provided = globals()[par]
            if provided != default:
                raise ValueError(
                    f"`{par}` was set to {provided} but `times` was also provided"
                )
        for time in times:
            window = Window(time, size, align, notes, skip)

            yield window

            skip = window.skip
            if skip == len(notes):
                break
    else:  # compute windows equally spaced by step
        match align:
            case "left":
                time = onset
            case "center":
                time = onset - size / 2
            case "right":
                time = onset - size
            case _:
                raise ValueError(f"Invalid value passed to `align`: {align}")
        while (offset is None) or (time < offset):
            window = Window(time, size, "left", notes, skip)

            yield window

            # if step == size, windows are back-to-back, so the next onset
            # is exactly equal to the previous offset. Avoid
            onset = window.offset if step == size else onset + step
            time += step
            skip = window.skip
            if skip == len(notes):
                break
