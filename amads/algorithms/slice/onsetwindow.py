"""Onset-time filtering for notes.

Filters notes whose onsets fall within a given time window.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=80
"""

from typing import Iterable, List, Optional, Union

from ...core.basics import Note, Score

__author__ = "Tai Nakamura"


def onset_window(
    passage: Union[Score, Iterable[Note]],
    min_time: float,
    max_time: float,
    timetype: Optional[str] = "quarters",
) -> List[Note]:
    """Filter notes by onset time within a half-open window.

    Returns notes whose onset times satisfy: ``min_time <= onset < max_time``.

    Parameters
    ----------
    passage : Score or Iterable[Note]
        The musical passage to be filtered.
    min_time : float
        Minimum limit of the window (inclusive) in quarters (default) or seconds
    max_time : float
        Maximum limit of the window (exclusive) in quarters (default) or seconds
    timetype (str, optional, default='quarters'):
        Time unit for calculation:
        - 'quarters': notes per quarter (default)
        - 'seconds' : notes per second
    Returns
    -------
    List[Note]
        Notes whose onsets are within the specified window ``[min_time, max_time)``

    Raises
    ------
    ValueError
        If timetype is not "quarters" or "seconds"

    Examples
    --------
    >>> from amads.core.basics import Score, Note
    >>> score = Score.from_melody([60, 62, 64, 65], onsets=[0.0, 1.0, 2.0, 3.0])
    >>> filtered = onset_window(score, 0.5, 2.5, timetype="quarters")
    >>> len(filtered)
    2
    >>> [n.pitch.key_num for n in filtered]
    [62, 64]
    """
    if timetype not in ("quarters", "seconds"):
        raise ValueError(
            f"Invalid timetype: '{timetype}'. " "Use 'quarters' or 'seconds'."
        )

    # Extract notes from the passage
    if isinstance(passage, Score):
        notes = passage.get_sorted_notes()
        score = passage
    else:
        notes = list(passage)
        score = None

    # Filter notes based on onset time
    filtered_notes = []
    for note in notes:
        onset_time = note.onset

        # Convert time if necessary
        if score is not None:
            if timetype == "seconds":
                if not score.units_are_seconds:
                    # Convert from quarters to seconds
                    onset_time = score.time_map.quarter_to_time(onset_time)
            else:  # timetype == "quarters"
                if score.units_are_seconds:
                    # Convert from seconds to quarters
                    onset_time = score.time_map.time_to_quarter(onset_time)

        # Check if onset is within the window (half-open interval)
        if min_time <= onset_time < max_time:
            filtered_notes.append(note)

    return filtered_notes
