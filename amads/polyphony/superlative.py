"""
In this directory:
- `skyline` returns a score with the highest sounding notes at any given point.
- `superlative` is similar, and designed to match the MIDI toolkit as exactly as possible.
- `envelope` is a variant on skyline that could be said to constitute a "smoothed" form,
    and (currently) operates on pitch-onset pairs only (analysis only, no score return).
- [this module] `superlative` is the most reductive, returning only the *single* highest/lowest/sharpest/flattest value.

This module author:
<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


from amads.core.basics import Score


def superlative(score: Score, attribute: str = "high") -> int:
    """
    Returns the superlative pitched Note from any score, as measured by one of four `attribute` options.

    The highest/lowest pair is relatively clear.
    This resembles the `skyline` functionality also in this module
    as well as the `superlative` function in in MIDI Toolbox
    (https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 61)
    except that this function returns the single highest/lowest note overall.

    To this logic we add another pair of options: the sharpest/flattest note,
    for that note who's pitch *spelling* is furthest along the spiral of fifths.

    Parameters
    ----------
    score : Score
        The polyphonic score to process.
    attribute : str. One of 4 options:
        "high" (default) or "low" by absolute pitch value (MIDI number, no spelling)
        or "sharp" or "flat" for that note who's pitch spelling is furthest along the spiral of fifths.
        Note that for the latter pair, the integer refers to the number of fifths from C,
        so F is -1 and G is plus 1, for example.

    Returns
    -------
    int
        The value in question.

    Examples
    --------
    >>> from amads.music import example
    >>> from amads.io.readscore import read_score
    >>> mid = read_score(example.fullpath("midi/sarabande.mid"))  # doctest: +ELLIPSIS
    Reading ...
    >>> superlative(mid, attribute="high")
    92
    >>> superlative(mid, attribute="low")
    62
    >>> superlative(mid, attribute="sharp")
    7
    >>> superlative(mid, attribute="flat")
    -4

    >>> superlative(mid, attribute="invalid_attribute")
    Traceback (most recent call last):
    ...
    ValueError: attribute must be one of ('high', 'low', 'sharp', 'flat'), got 'invalid_attribute'

    """

    valid_attributes = ("high", "low", "sharp", "flat")
    attribute = attribute.lower()
    if attribute not in valid_attributes:
        raise ValueError(
            f"attribute must be one of {valid_attributes}, got {attribute!r}"
        )

    flat_score = score.flatten()
    notes = flat_score.get_sorted_notes()

    if len(notes) < 2:
        raise ValueError(
            "Only call this function on cases with at least two notes."
        )

    if attribute in ("high", "low"):
        current = notes[0].pitch.key_num
    elif attribute in ("sharp", "flat"):
        current = notes[0].pitch.fifths_from_c

    for note in notes[1:]:
        if attribute == "high" and note.pitch.key_num > current:
            current = note.pitch.key_num
        elif attribute == "low" and note.pitch.key_num < current:
            current = note.pitch.key_num
        elif attribute == "sharp" and note.pitch.fifths_from_c > current:
            current = note.pitch.fifths_from_c
        elif attribute == "flat" and note.pitch.fifths_from_c < current:
            current = note.pitch.fifths_from_c

    return current
