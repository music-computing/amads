"""Onset-time filtering for notes.

Filters notes whose onsets fall within a given time window.
"""

from typing import Iterable, List, Union

from ...core.basics import Note, Score


def onset_window(
    passage: Union[Score, Iterable[Note]],
    min_time: float,
    max_time: float,
    miditoolbox_compatible: bool = False,
) -> List[Note]:
    """Filter notes by onset time within a time window.

    By default, returns notes whose onset times satisfy
    ``min_time <= onset < max_time`` (half-open interval).

    ``min_time`` and ``max_time`` must use the same time units as the
    onsets in ``passage``. For a [Score][amads.core.basics.Score], call
    [convert_to_seconds][amads.core.basics.Score.convert_to_seconds] or
    [convert_to_quarters][amads.core.basics.Score.convert_to_quarters]
    before calling this function if you need bounds in a different unit.
    This function does not modify the score or convert note onsets.

    When ``passage`` is an iterable of notes, bounds must match each
    note's ``onset`` units

    <small>**Author**: Tai Nakamura</small>

    Parameters
    ----------
    passage : Score or Iterable[Note]
        The musical passage to be filtered.
    min_time : float
        Minimum limit of the window (inclusive), in the same units as
        note onsets in ``passage``.
    max_time : float
        Maximum limit of the window. Exclusive by default; inclusive when
        ``miditoolbox_compatible`` is True.
    miditoolbox_compatible : bool, optional
        If False (default), use a half-open window ``[min_time, max_time)``.
        If True, match Matlab MIDI Toolbox ``onsetwindow`` behavior with a
        closed window ``[min_time, max_time]``.

    Returns
    -------
    List[Note]
        Notes whose onsets fall within the specified window.

    Examples
    --------
    >>> from amads.core.basics import Score
    >>> score = Score.from_melody([60, 62, 64, 65], onsets=[0.0, 1.0, 2.0, 3.0])
    >>> filtered = onset_window(score, 0.5, 2.5)
    >>> len(filtered)
    2
    >>> [n.pitch.key_num for n in filtered]
    [62, 64]

    References
    ----------
    - Toiviainen, P., & Eerola, T. (2016). MIDI Toolbox 1.1. URL: https://github.com/miditoolbox/1.1
      The ``onsetwindow`` function is
      documented on p. 81 of the manual:
      https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf
    """
    if isinstance(passage, Score):
        notes = passage.get_sorted_notes()
    else:
        notes = list(passage)

    filtered_notes = []
    for note in notes:
        onset_time = note.onset
        if miditoolbox_compatible:
            in_window = min_time <= onset_time <= max_time
        else:
            in_window = min_time <= onset_time < max_time
        if in_window:
            filtered_notes.append(note)

    return filtered_notes
