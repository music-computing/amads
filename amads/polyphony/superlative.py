"""
In this directory:
- `skyline` returns a score with the highest sounding notes at any given point.
- `extreme` is similar, and designed to match the MIDI toolkit as exactly as possible.
- `envelope` is a variant on skyline that could be said to constitute a "smoothed" form,
    and (currently) operates on pitch-onset pairs only (analysis only, no score return).
- [this module] `superlative` is the most reductive, returning only the *single* highest/lowest/sharpest/flattest value.

This module author:
<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


from amads.core.basics import Note, Score


def superlative(score: Score, attribute: str = "high") -> int:
    """
    Returns an integer relating to the one of four `attribute` options
    for "superlative" pitched Note from any score, as measured by that attribute.

    The highest/lowest pair is relatively clear.
    This broadly resembles the `skyline` and `extreme` functionality also in this module,
    except that this function returns the single highest/lowest note overall rather than a score.

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

    notes = score.find_all(Note)

    if attribute == "high":
        return max(notes, key=lambda n: n.pitch.key_num).pitch.key_num
    elif attribute == "low":
        return min(notes, key=lambda n: n.pitch.key_num).pitch.key_num
    elif attribute == "sharp":
        return max(
            notes, key=lambda n: n.pitch.fifths_from_c
        ).pitch.fifths_from_c
    elif attribute == "flat":
        return min(
            notes, key=lambda n: n.pitch.fifths_from_c
        ).pitch.fifths_from_c
