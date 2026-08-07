"""
Key-aware tonal stability with per-note annotation.

After estimating the best-matching profile and key with
[kkkey][amads.pitch.key.kkkey.kkkey], each note receives the profile weight
for its pitch class (profile rotated to the estimated ``key_index``).

AMADS-native API. For a MIDI Toolbox-compatible list return, see
[tonality][amads.pitch.key.tonality.tonality].

<small>**Author**: Tai Nakamura</small>

Reference
---------
https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 93.
"""

from typing import List, Optional, Tuple

import amads.pitch.key.profiles as prof
from amads.core.basics import Note, Score
from amads.pitch.key.kkkey import kkkey


def _weights_for_key(
    profile: prof.KeyProfile, attribute: str, key_index: int
) -> List[float]:
    """Return 12 stability weights (pitch class 0=C … 11=B) for ``attribute`` at ``key_index``."""
    if key_index < 0 or key_index > 11:
        raise ValueError(f"key_index must be 0..11, got {key_index}")
    pitch_profile = getattr(profile, attribute, None)
    if not isinstance(pitch_profile, prof.PitchProfile):
        raise ValueError(
            f"profile {profile.name!r} has no PitchProfile attribute "
            f"{attribute!r}"
        )
    row = pitch_profile.as_canonical_matrix()[key_index]
    return [float(value) for value in row]


def tonal_stability(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    *,
    attribute_names: Optional[List[str]] = None,
    salience_flag: bool = False,
    stability_prop_name: str = "tonal_stability",
    key: Optional[Tuple[str, int]] = None,
) -> Score:
    """Annotate each note with tonal stability from an estimated key.

    Calls [kkkey][amads.pitch.key.kkkey.kkkey] to choose a profile attribute
    and ``key_index``, looks up profile weights by pitch class, and stores
    each value with ``note.set(stability_prop_name, value)`` on notes from
    [find_all][amads.core.basics.EventGroup.find_all] ``(Note)``.

    Parameters
    ----------
    score : Score
        The musical passage to analyze (modified in place via ``note.info``).
    profile : KeyProfile, optional
        Key profiles for estimation and stability weights (default
        ``profiles.krumhansl_kessler``).
    attribute_names : list of str, optional
        Profile attributes passed to [kkkey][amads.pitch.key.kkkey.kkkey].
        ``None`` (default) means all pitch-profile attributes on ``profile``.
        Passed through to ``kkkey``; see that function for details.
    salience_flag : bool, optional
        Passed to [kkkey][amads.pitch.key.kkkey.kkkey]. Default is ``False``.
    stability_prop_name : str, optional
        Note property name for the stability value. Default is
        ``"tonal_stability"``. Use distinct names to store results from
        different profiles on the same score.
    key : tuple of (str, int), optional
        Fixed ``(attribute_name, key_index)`` as returned by
        [kkkey][amads.pitch.key.kkkey.kkkey], with ``key_index`` in ``0..11``
        where 0 is C. When set, key estimation is skipped.

    Returns
    -------
    Score
        The same score, with stability values stored on each note. Tied note
        segments are annotated separately (ties are not merged).

    Raises
    ------
    ValueError
        If a note has no defined pitch, or ``key`` / the estimated attribute
        does not name a pitch profile on ``profile``.

    See Also
    --------
    tonality : MIDI Toolbox-compatible stability list (key of C assumed).
    kkkey : Estimate the key of a score.
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
    >>> from amads.core.basics import Score, Note
    >>> score = Score.from_melody([60, 62, 63, 65, 67, 68, 70, 72])
    >>> tonal_stability(
    ...     score,
    ...     profile=prof.vuvan,
    ...     attribute_names=["natural_minor"],
    ... ) is score #check in-place
    True
    >>> next(score.find_all(Note)).get("tonal_stability")
    5.08
    """
    notes: List[Note] = list(score.find_all(Note))
    if not notes:
        return score

    if key is None:
        attribute, key_index = kkkey(
            score,
            profile=profile,
            attribute_names=attribute_names,
            salience_flag=salience_flag,
        )
    else:
        attribute, key_index = key

    weights = _weights_for_key(profile, attribute, key_index)
    for note in notes:
        if note.pitch is None or note.pitch.key_num is None:
            raise ValueError(
                "tonal_stability requires notes with defined pitch"
            )
        pc = int(note.pitch.key_num) % 12
        note.set(stability_prop_name, float(weights[pc]))

    return score
