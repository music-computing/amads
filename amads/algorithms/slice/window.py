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
    """A fixed-size window of a musical score.

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
        Notes to consider for inclusion in this window, sorted by start time and pitch
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

            if note.end < start:
                # The note finished before the window started.
                # It'll definitely finish before future windows start,
                # because they'll be even later, so we can skip it then too.
                skip = i
                continue

            if note.start > end:
                # The note starts after the window finishes.
                # All the remaining notes in candidate_notes will have even later starts,
                # so we don't need to check them for this window.
                # They might be caught by future windows though.
                break

            original_notes.append(note)

            # We use copy instead of creating a new Note because we want to
            # preserve any other attributes that might be useful in downstream tasks.
            note = note.copy()
            note.start = max(note.start, start)
            note.end = min(note.end, end)

            notes.append(note)

        # The next window can look at this attribute to know which candidates can be skipped.
        self.skip = skip

        super().__init__(
            content=notes,
            original_notes=original_notes,
            delta=start,
            duration=size,
        )


def sliding_window(
    passage: Union[Score, Iterable[Note]],
    size: float,
    step: float = 1.0,
    align: str = "right",
    start: float = 0.0,
    end: Optional[float] = None,
    times: Optional[Iterable[float]] = None,
) -> Iterator[Window]:
    """Slice a score into (possibly overlapping) windows of a given size.

    Parameters
    ----------
    passage : Score or Iterable[Note]
        The musical passage to be windowed
    size : float
        The size of each window (time units)
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
    start : float, default=0.0
        The desired time of the first window
    end : float, optional
        If set, the windowing will stop once the end time is reached.
        Following the behaviour of Python's built-in range function,
        ``end`` is not treated inclusively, i.e. the last window will
        not include ``end``
    times : Iterable[float], optional
        Optional iterable of times to generate windows for. If provided,
        `start` and `end` are ignored

    Returns
    -------
    Iterator[Window]
        Iterator over the windows
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
    notes.sort(key=lambda n: (n.start, n.pitch))

    if times is None:
        window_times = float_range(start, end, step)
    else:
        for par, default in [("start", 0.0), ("end", None), ("step", 1.0)]:
            provided = globals()[par]
            if provided != default:
                raise ValueError(
                    f"`{par}` was set to {provided} but `times` was also provided"
                )

        window_times = times

    skip = 0

    for time in window_times:
        window = Window(time, size, align, notes, skip)

        yield window

        skip = window.skip

        if skip + 1 == len(notes):
            break
