from typing import Dict

from amads.algorithms.mtype_tokenizer import FantasticTokenizer
from amads.algorithms.ngrams import NGramCounter
from amads.core.basics import Note, Score
from amads.melody.contour.interpolation_contour import InterpolationContour
from amads.melody.contour.step_contour import StepContour
from amads.melody.segment import fantastic_segmenter


def fantastic_count_mtypes(
    score: Score, segment: bool, phrase_gap: float, units: str
) -> Dict:
    """Count M-Types in a melody.

    Parameters
    ----------
    score : Score
        The score to count M-Types in.
    segment : bool
        Whether to segment the melody into phrases.
    phrase_gap : float
        The minimum IOI gap to consider a new phrase.
    units : str
        The units of the phrase gap, either "seconds" or "quarters".

    Returns
    -------
    Dict
        A dictionary of M-Type counts.
    """
    if segment:
        segments = fantastic_segmenter(score, phrase_gap, units)
    else:
        segments = [score]

    counter = NGramCounter()
    tokenizer = FantasticTokenizer()

    all_tokens = []
    for phrase in segments:
        tokenizer.tokenize(phrase)
        all_tokens.extend(tokenizer.tokens)

    counter.count_ngrams(all_tokens, n=[1, 2, 3, 4, 5])

    return counter.ngram_counts


def fantastic_interpolation_contour_features(score: Score) -> Dict:
    """Extract interpolation contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract interpolation contour features from.

    Returns
    -------
    Dict
        A dictionary of interpolation contour features.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Extract pitches and times for contour calculation
    pitches = [note.pitch.keynum for note in notes]
    times = [note.onset for note in notes]

    # Calculate contour
    ic = InterpolationContour(pitches, times, method="fantastic")

    return {
        # Interpolation contour features
        "global_direction": ic.global_direction,
        "mean_gradient": ic.mean_gradient,
        "gradient_std": ic.gradient_std,
        "direction_changes": ic.direction_changes,
        "class_label": ic.class_label,
    }


def fantastic_step_contour_features(score: Score) -> Dict:
    """Extract step contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract step contour features from.

    Returns
    -------
    Dict
        A dictionary of step contour features.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Extract pitches and times for contour calculation
    pitches = [note.pitch.keynum for note in notes]
    durations = [note.duration for note in notes]

    sc = StepContour(pitches, durations)

    return {
        "global_variation": sc.global_variation,
        "global_direction": sc.global_direction,
        "local_variation": sc.local_variation,
    }
