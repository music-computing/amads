"""
Implementation of the quantize() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 85

"""

from typing import cast

from amads.core.basics import Score
from amads.time.dropshortnotes import dropshortnotes


def quantize(
    score: Score,
    onsetres: float = 1 / 8,
    durres: float | None = None,
    filterres: float | None = None,
    filter: bool = False,
) -> Score:
    """
    Quantize note events in a score according to onset resolution,
    duration resolution, and optionally filter out short note events.

    This function returns a new flattened score that has been quantized.
    Tied note chains are handled correctly: each note's onset is
    preserved and the chain is trimmed or adjusted as needed before
    merging.

    This is an implementation of the quantize function in the Matlab
    MIDI Toolbox.

    Parameters
    ----------
    score : Score
        The input score to be quantized.
    onsetres : float
        The grid resolution for onsets, in Matlab MIDI Toolbox compatible
        units where 1/8 means "eighth note", etc.
    durres : float or None
        The grid resolution for durations. If not provided, defaults to
        onset_divisions (see note on MIDI Toolbox Compatibility).
    filterres : float or None
        If provided, any note with a duration strictly less than
        `filterres` (including all ornaments) will be removed as if
        after quantization.

    Returns
    -------
    Score
        A new, flattened, and quantized score.

    Matlab MIDI Toolbox compatibility
    ---------------------------------
    AMADS does not emulate all cases of MIDI Toolbox `quantize` because
    AMADS quantization never rounds a duration to zero. It uses a
    minimum duration of 1 division quantum instead. Ignoring this
    detail, implementations are compatible as described below, and when
    the Toolbox `filterres` parameter enables filtering short notes,
    AMADS emulation of `quantize` is exact because all notes that would
    round to zero in the Toolbox implementation can be removed by AMADS.

    When Toolbox `quantize` is called with only the `nmat` argument,
    call AMADS `quantize(score, 1/8, 1/16)`.  The Toolbox specification
    says `durres` will be double `onsetres`, but the Toolbox
    implementation interprets *double* to mean "twice as fine" or
    numerically half the quantum size.

    When Toolbox `quantize` is called with `nmat` and `onsetres`, call
    AMADS `quantize(score, onsetres, 0.5 * onsetres)` to match the
    Toolbox specification. However, the Toolbox implementation seems to
    have an error in that it does not quantize duration at all in this
    case. For AMADS, the closest approximation would be using a small
    `durres`, e.g., `quantize(score, onsetres, 1/2880)` to minimize or
    eliminate any duration quantization.

    When Toolbox `quantize` is called with `nmat`, `onsetres`, and
    `durres`, call AMADS with the same parameters: `quantize(score,
    onsetres, durres)` to match the Toolbox specification.

    To get Toolbox `quantize` behavior when all four parameters are
    given, call AMADS with the same parameters. As mentioned above,
    This is the only case where AMADS `quantize` should always return
    equivalent results.
    """
    if durres is None:
        durres = onsetres
    if filterres is not None:
        score = dropshortnotes(score, max(filterres, 0.5 * durres) * 4)
    else:  # copy so tied chains are intact when quantize runs
        score = cast(Score, score.copy())

    # convert resolutions to divisions per quarter, e.g., 1/8 -> 2
    score.quantize(round(0.25 / onsetres), round(0.25 / durres))

    return score
