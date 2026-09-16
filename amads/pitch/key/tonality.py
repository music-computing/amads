"""
Tonal stability of notes in a melody using key-profile weights.

After estimating major/minor mode with [keymode][amads.pitch.key.keymode.keymode],
each note receives the Krumhansl--Kessler profile weight for its pitch class.
Profiles are not rotated to an estimated key: weights are those of C major or
C minor, matching the MIDI Toolbox ``tonality`` behavior (same assumption as
``keymode``).

MIDI Toolbox-compatible port. For key-aware stability with per-note annotation,
see [tonal_stability][amads.pitch.key.tonal_stability.tonal_stability].

<small>**Author**: Tai Nakamura</small>

Reference
---------
https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 93.
"""

import warnings
from typing import List

import amads.pitch.key.profiles as prof
from amads.core.basics import Note, Score
from amads.pitch.key.keymode import keymode


def _mode_from_keymode_result(modes: List[str]) -> str:
    """Map keymode output to a mode label for C-aligned weight lookup."""
    if modes == ["major"]:
        return "major"
    if modes == ["minor"]:
        return "minor"
    return "unspecified"


def _weights_c_tonic(mode: str) -> List[float]:
    """Return unrotated Krumhansl--Kessler weights for C major or C minor."""
    if mode == "major":
        return list(prof.krumhansl_kessler.major.data)
    if mode == "minor":
        return list(prof.krumhansl_kessler.minor.data)
    warnings.warn(
        "Key mode not specified (major=1, minor=2)",
        stacklevel=3,
    )
    return list(prof.krumhansl_kessler.major.data)


def _stability_for_note(note: Note, weights: List[float]) -> float:
    """Return the stability value for a note."""
    if note.pitch is None or note.pitch.midi_num is None:
        raise ValueError("tonality requires notes with defined pitch")
    pc = int(note.pitch.midi_num) % 12
    return float(weights[pc])


def tonality(
    score: Score,
    salience_flag: bool = False,
) -> List[float]:
    """Tonal stability rating for each note in a score.

    Calls [keymode][amads.pitch.key.keymode.keymode] to choose major or minor,
    then looks up unrotated Krumhansl--Kessler profile weights by pitch class
    (C major or C minor profiles, not rotated to the score's key).

    Parameters
    ----------
    score : Score
        The musical passage to analyze.
    salience_flag : bool, optional
        Passed to [keymode][amads.pitch.key.keymode.keymode]. Default is
        ``False``.

    Returns
    -------
    list of float
        Stability value per sounding note (the first note of each tied
        group).

    See Also
    --------
    keymode : Estimate major/minor mode (key of C assumed).
    tonal_stability : Key-aware stability with per-note annotation.
    profiles : Key profile data, including ``krumhansl_kessler``.

    References
    ----------
    - Krumhansl, C. L. (1990). Cognitive Foundations of Musical Pitch.
      New York: Oxford University Press.
    - Toiviainen, P., & Eerola, T. (2016). MIDI Toolbox 1.1.
      https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 93.

    Examples
    --------
    >>> import amads.pitch.key.profiles as prof
    >>> from amads.core.basics import Score
    >>> score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    >>> values = tonality(score)
    >>> values[0] == prof.krumhansl_kessler.major.data[0]
    True
    """
    notes: List[Note] = score.get_sorted_notes()
    if not notes:
        return []

    modes = keymode(
        score,
        profile=prof.krumhansl_kessler,
        attribute_names=["major", "minor"],
        salience_flag=salience_flag,
    )
    mode = _mode_from_keymode_result(modes)
    weights = _weights_c_tonic(mode)

    result: List[float] = []
    for note in notes:
        result.append(_stability_for_note(note, weights))
    return result
