"""
Tonal stability of notes in a melody using key-profile weights.

After estimating major/minor mode with :func:`~amads.pitch.key.keymode.keymode`,
each note receives the profile weight for its pitch class (tonic C assumed).
"""

import warnings
from typing import List

import amads.pitch.key.profiles as prof
from amads.core.basics import Note, Score
from amads.pitch.key.keymode import keymode


def _profile_weights_for_mode(
    profile: prof.KeyProfile, mode: str
) -> List[float]:
    if mode == "major":
        pitch_profile = profile.major
    elif mode == "minor":
        pitch_profile = profile.minor
    else:
        raise ValueError(f"unsupported mode {mode!r}")
    return list(pitch_profile.data)


def tonality(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    salience_flag: bool = False,
) -> List[float]:
    """Tonal stability rating for each note in a score.

    Calls :func:`~amads.pitch.key.keymode.keymode` to choose major or minor, then
    looks up Krumhansl--Kessler-style profile weights by pitch class (MIDI Toolbox
    ``tonality`` with ``refstat('kkmaj')`` / ``refstat('kkmin')``).

    <small>**Author**: Tai Nakamura</small>

    Parameters
    ----------
    score : Score
        The musical passage to analyze.
    profile : KeyProfile, optional
        Key profiles for mode estimation and stability weights. Default is
        :data:`~amads.pitch.key.profiles.krumhansl_kessler` (MIDI Toolbox
        ``kkmaj`` / ``kkmin``).
    salience_flag : bool, optional
        Passed to :func:`~amads.pitch.key.keymode.keymode`. Default is ``False``.

    Returns
    -------
    list of float
        Stability value per note, in the same order as
        :meth:`~amads.core.basics.Score.get_sorted_notes`.

    See Also
    --------
    keymode
    amads.pitch.key.profiles.krumhansl_kessler

    References
    ----------
    - Krumhansl, C. L. (1990). *Cognitive Foundations of Musical Pitch*.
      New York: Oxford University Press.
    - Toiviainen, P., & Eerola, T. (2016). MIDI Toolbox 1.1. URL:
      https://github.com/miditoolbox/1.1

    Examples
    --------
    >>> from amads.core.basics import Score
    >>> score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    >>> len(tonality(score)) == 8
    True
    """
    notes: List[Note] = score.get_sorted_notes()
    if not notes:
        return []

    modes = keymode(
        score,
        profile=profile,
        attribute_names=["major", "minor"],
        salience_flag=salience_flag,
    )
    if modes == ["major"]:
        weights = _profile_weights_for_mode(profile, "major")
    elif modes == ["minor"]:
        weights = _profile_weights_for_mode(profile, "minor")
    else:
        warnings.warn(
            "Key mode not clearly major or minor; using major profile weights "
            f"(keymode returned {modes!r}).",
            stacklevel=2,
        )
        weights = _profile_weights_for_mode(profile, "major")

    result: List[float] = []
    for note in notes:
        if note.pitch is None or note.pitch.key_num is None:
            raise ValueError("tonality requires notes with defined pitch")
        pc = int(note.pitch.key_num) % 12
        result.append(weights[pc])
    return result
