"""
Melodic distance according to features extracted from those melodies.

Completely rewrites the original calculate_melodic_distance function that
Yiwen Zhao first wrote.

Ports the `meldistance` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 70.
"""

from itertools import islice
from statistics import mean

import numpy as np

from amads.algorithms.nnotes import nnotes
from amads.algorithms.norm import pnorm_distance
from amads.core.basics import Note, Score
from amads.melody.contour.combcontour import get_pitch_comparison_contour_matrix
from amads.melody.contour.melcontour import melodySamplingContour

# ivdist1, ivdist2, pcdist1, pcdist2
from amads.pitch.ivdist1 import interval_distribution_1
from amads.pitch.ivdist2 import interval_distribution_2
from amads.pitch.pcdist1 import pitch_class_distribution_1
from amads.pitch.pcdist2 import pitch_class_distribution_2
from amads.time.durdist1 import duration_distribution_1
from amads.time.durdist2 import duration_distribution_2

distribution_repr = [
    "ivdist1",
    "ivdist2",
    "pcdist1",
    "pcdist2",
    "durdist1",
    "durdist2",
]
melcontour_repr = "melcontour"
combcontour_repr = "combcontour"
all_reprs = distribution_repr + [melcontour_repr, combcontour_repr]


def melodic_distance(
    score1: Score,
    score2: Score,
    repr: str = "pcdist1",
    metric: str = "taxi",
    samples: int = 10,
    rescale: bool = False,
    miditoolbox_compatible: bool = False,
) -> float | None:
    """
    Measurement of distance between specified feature data extracted from two
    Score objects.

    Parameters
    ----------
    score1 : Score
        The first Score object.
    score2 : Score
        The second Score object.
    repr : str
        Feature extraction function used for distance measuring.
    metric : str
        There are two options here:
        (1) A norm metric as specified in norm.py
        (2) "cosine" to specify the angle between the two vectors obtained
        from repr.
    samples : int
        Number of samples for contour representation.
    rescale : bool
        Rescale distance to similarity value between 0 and 1.
    miditoolbox_compatible : bool
        Whether or not we want the result to be compatible with the original
        matlab implementation of miditoolbox

    Returns
    -------
    float | None
        Value representing the distance between the two scores under the given
        representation and metric.
        None if cannot be calculated

    Raises
    ------
    ValueError
        if argument combination is not supported
    """
    if repr == "pcdist1":
        dist1 = pitch_class_distribution_1(
            score1, miditoolbox_compatible=miditoolbox_compatible
        )
        dist2 = pitch_class_distribution_1(
            score2, miditoolbox_compatible=miditoolbox_compatible
        )
        data_vector_1 = np.array(dist1.data)
        data_vector_2 = np.array(dist2.data)
    elif repr == "pcdist2":
        dist1 = pitch_class_distribution_2(
            score1, miditoolbox_compatible=miditoolbox_compatible
        )
        dist2 = pitch_class_distribution_2(
            score2, miditoolbox_compatible=miditoolbox_compatible
        )
        data_vector_1 = np.array(dist1.data)
        data_vector_2 = np.array(dist2.data)
    elif repr == "ivdist1":
        dist1 = interval_distribution_1(
            score1, miditoolbox_compatible=miditoolbox_compatible
        )
        dist2 = interval_distribution_1(
            score2, miditoolbox_compatible=miditoolbox_compatible
        )
        data_vector_1 = np.array(dist1.data)
        data_vector_2 = np.array(dist2.data)
    elif repr == "ivdist2":
        dist1 = interval_distribution_2(
            score1, miditoolbox_compatible=miditoolbox_compatible
        )
        dist2 = interval_distribution_2(
            score2, miditoolbox_compatible=miditoolbox_compatible
        )
        data_vector_1 = np.array(dist1.data)
        data_vector_2 = np.array(dist2.data)
    elif repr == "durdist1":
        dist1 = duration_distribution_1(
            score1, miditoolbox_compatible=miditoolbox_compatible
        )
        dist2 = duration_distribution_1(
            score2, miditoolbox_compatible=miditoolbox_compatible
        )
        data_vector_1 = np.array(dist1.data)
        data_vector_2 = np.array(dist2.data)
    elif repr == "durdist2":
        dist1 = duration_distribution_2(
            score1, miditoolbox_compatible=miditoolbox_compatible
        )
        dist2 = duration_distribution_2(
            score2, miditoolbox_compatible=miditoolbox_compatible
        )
        data_vector_1 = np.array(dist1.data)
        data_vector_2 = np.array(dist2.data)
    elif repr == "melcontour":
        if samples <= 0:
            raise ValueError(
                f"invalid sample number {samples} with {repr} option!"
            )
        note_list1 = melodySamplingContour(score1, samples, "rel")
        note_list2 = melodySamplingContour(score2, samples, "rel")
        if not note_list1 or not note_list2:
            return None
        mean1 = mean(note.midi_num for note in note_list1)
        mean2 = mean(note.midi_num for note in note_list2)
        data_vector_1 = np.fromiter(
            (note.midi_num - mean1 for note in note_list1), int
        )
        data_vector_2 = np.fromiter(
            (note.midi_num - mean2 for note in note_list2), int
        )
    elif repr == "combcontour":
        score1_len = nnotes(score1)
        score2_len = nnotes(score2)
        mtx_len = min(score1_len, score2_len)
        if not mtx_len:
            return None
        comb_mtx_1 = get_pitch_comparison_contour_matrix(
            islice(score1.find_all(Note), mtx_len)
        )
        comb_mtx_2 = get_pitch_comparison_contour_matrix(
            islice(score2.find_all(Note), mtx_len)
        )
        abs_diff_mtx = abs(comb_mtx_1.astype(int) - comb_mtx_2.astype(int))
        distance = np.sum(abs_diff_mtx) / (mtx_len * mtx_len - mtx_len)
        if rescale:
            rescale_val = 0.5
            if distance < rescale_val:
                distance = 2 * (rescale_val - distance) + distance
            else:
                # there is a bug in the matlab miditoolbox version,
                # namely the formula is functionally equivalent to the previous
                # branch (when distance < rescale_val)
                # Anyways, that 'potential' bug is reproduced here...
                distance = 2 * (rescale_val - distance) + distance
        return float(distance)
    else:
        raise ValueError("Unsupported representation type.")

    rescale_val = 0
    if metric == "taxi":
        distance = pnorm_distance(data_vector_1, data_vector_2, 1)
        if repr in distribution_repr:
            rescale_val = 1
        elif repr == melcontour_repr:
            rescale_val = 8 * samples
    elif metric == "euc":
        distance = pnorm_distance(data_vector_1, data_vector_2, 2)
        if repr in distribution_repr:
            rescale_val = 1
        elif repr == melcontour_repr:
            rescale_val = 2 * samples
    elif metric == "cosine":
        distance = np.sum(data_vector_1.conj() * data_vector_2, axis=0) / (
            np.linalg.norm(data_vector_1) * np.linalg.norm(data_vector_2)
        )
        distance = np.sum(distance)
        if repr in distribution_repr:
            rescale_val = 0.15
        elif repr == melcontour_repr:
            rescale_val = 15 * samples
            distance += 11 * samples
    else:
        raise ValueError(f"Unsupported metric type {metric}!")

    if rescale:
        if repr in distribution_repr:
            if distance < rescale_val:
                distance = (2 * (rescale_val - distance) + distance) / 2
            else:
                # there is a bug in the matlab miditoolbox version,
                # namely the formula is functionally equivalent to the previous
                # branch (when distance < rescale_val)
                # Anyways, that 'potential' bug is reproduced here...
                distance = (2 * (rescale_val - distance) + distance) / 2
        elif repr == melcontour_repr:
            if distance < rescale_val:
                distance = (2 * rescale_val - distance) / (2 * rescale_val)
            else:
                distance = (distance - 2 * (distance - rescale_val)) / (
                    2 * rescale_val
                )
        else:
            raise ValueError(f"unimplemented option {repr}!")

    return float(distance)
