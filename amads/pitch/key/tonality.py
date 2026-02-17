"""
transposes a given score to C after we've attained
the maximum correlation key of the score from
the krumhansl-kessler algorithm (kkcc with default parameters).
Computes the tonal stability ratings for tones in the melody after
determining its key mode (major/minor) with keymode.

This function matches the behavior of the original miditoolbox function
and only uses Krumhansl Kessler key profile. However, alternative profiles
for major and minor keys may be used if this function's behavior is slightly
modified.

References
----------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=92 for more details

TODO: literature references
"""

from amads.core.basics import Score
from amads.pitch.key import profiles
from amads.pitch.key.keymode import keymode
from amads.pitch.ismonophonic import ismonophonic

def tonality(score: Score) -> profiles.PitchProfile:
    """
    Returns the pitch profile, that
    best describes the tonality (in 'major' or 'minor') of the given music score
    according to krumhansl-kessler pitch analysis.

    Parameters
    ----------
    score: Score
        The musical score to analyze.

    See Also
    --------
    keymode

    Returns
    -------
    PitchProfile
        The pitch profile that best describes the tonality of the score
        that was analyzed.
    """
    if not ismonophonic(score):
        raise ValueError("score must be monophonic for this function to " \
        "be valid")
    modes = keymode(score)
    if (len(modes) != 1):
        raise ValueError("score is ambiguous in finding the modality of" \
        "its key")
    mode = modes[0]
    if (mode == "major"):
        return profiles.krumhansl_kessler["major"]
    elif (mode == "minor"):
        return profiles.krumhansl_kessler["minor"]
    else:
        return profiles.krumhansl_kessler["major"]