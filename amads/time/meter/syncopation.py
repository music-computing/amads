"""
Measurement of syncopation from the literature,
notably WNBD (weighted note-to-beat distance).

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"

import logging
from fractions import Fraction
from typing import Optional

from partitura import load_score

log = logging.getLogger(__name__)


class SyncopationMetric:
    def __init__(self, path_to_score: Optional[str] = None):
        """
        The methods of this class implement syncopation metrics from the
        literature. These are typically based on simple data (note start
        times and similar).

        The parameters of this class allow users to run from a score
        (with onsets etc. deduced from there) or directly on their own
        data (the necessary parameters differ slightly for each method).

        Parameters
        ----------
        path_to_score:
            Path to the score in any supported format (e.g., MusicXML).
            Warning: Partitura takes "beats" from time signature
            denominators, e.g., 6/8 has 6 "beats" (not 2).
        """
        self.path_to_score = path_to_score
        self.note_array = None

    def load_note_array_from_score(self):
        """
        Parse a score and return Partitura's `.note_array()` with `include_metrical_position=True`.
        (NOTE: this direct use of Partitura may change in future in favour of user-specified preference.)

        This should cover the required information.
        The note array's fields includes several fields of which methods here
        use the following (in their words):

        * 'onset_beat': onset time of the note in beats
        * 'duration_beat': duration of the note in beats

        These values are called in the form `note_array["onset_beat"]`.

        """
        if self.note_array is not None:
            log.debug("note array already retrieved, skipping")
            return
        if self.path_to_score is None:
            raise ValueError("No score provided.")
        else:
            score = load_score(self.path_to_score)
            self.note_array = score.note_array(include_metrical_position=True)

    def weighted_note_to_beat_distance(
        self,
        onset_beats: Optional[list] = None,
        cycle_length: Optional[Fraction] = None,
    ) -> Fraction:
        """
        The weighted note-to-beat distance measure (WNBD)
        measures the distance between note starts and
        records the traversing of beats, and the distance to the nearest beat.

        The authors clarify that "notes are supposed to end where the
        next note starts", so we're working with the inter-note interval
        (INI), aka inter-onset interval (IOI), rather than any durations.

        Parameters
        ----------
        onset_beats:
            User supplied data for the onset time of each note expressed
            in beats. Optional.
        cycle_length: # TODO review this value and naming convention.
            Length of the rhythmic cycle in beats (e.g. Fraction(4, 1) for
            a 4-beat bar). If provided, the *last* onset's inter-onset
            interval is computed by wrapping around to
            ``onset_beats[0] + cycle_length`` -- i.e. this treats the
            rhythm as cyclic/repeating, which is how all the standard
            "world sample" test rhythms are defined.

        Returns
        -------
        WNBD value (Fraction)

        Examples
        --------
        >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]
        >>> onset_beats = vector_to_onset_beat(vector=son, beat_unit_length=4)
        >>> sm = SyncopationMetric()
        >>> sm.weighted_note_to_beat_distance(onset_beats=onset_beats)
        Fraction(14, 5)

        >>> hesitation = [1, 0, 1, 0, 1, 0, 0, 1]
        >>> onset_beats = vector_to_onset_beat(vector=hesitation, beat_unit_length=4)
        >>> sm = SyncopationMetric()
        >>> sm.weighted_note_to_beat_distance(onset_beats=onset_beats)
        Fraction(1, 2)

        >>> from amads.music import example
        >>> test_xml_file = str(example.fullpath("musicxml/ex1.xml"))
        >>> sm = SyncopationMetric(path_to_score=test_xml_file)
        >>> sm.weighted_note_to_beat_distance()
        Fraction(4, 3)

        """
        # onset_beats is required for user-provided,
        if onset_beats is None:  # if not seek a score on the class
            if self.path_to_score is not None:
                self.load_note_array_from_score()
                onset_beats = [
                    Fraction(float(x["onset_beat"])) for x in self.note_array
                ]  # type: ignore
                # Sic, Fraction via first: Partitura uses np.float32 and
                #    Fractions do not accept that type.
                # TODO revisit class handling of this retrieval if combining more algos.
            else:
                raise ValueError("No score or user values provided.")

        if cycle_length is not None:
            # Cyclic: wrap the final onset back to a virtual next cycle so the last source onset gets a real IOI.
            extended = list(onset_beats) + [onset_beats[0] + cycle_length]
            n_notes_to_process = len(onset_beats)
        else:
            # Last onset has no successor and is silently skipped. Probably no good use for this.
            extended = list(onset_beats)
            n_notes_to_process = len(onset_beats) - 1

        durations = [j - i for i, j in zip(extended[:-1], extended[1:])]

        per_note_syncopation_values = []
        for i in range(n_notes_to_process):
            onset = onset_beats[i]
            if int(onset) == onset:  # starts on a beat
                per_note_syncopation_values.append(0)
                continue

            duration = durations[i]
            this_beat_int = int(onset)  # NB round down
            end = onset + duration

            if end <= this_beat_int + 1:
                numerator = 1
            elif end < this_beat_int + 2:
                numerator = 2
            else:
                # TODO: test_meter_profiles includes a test case from the paper of `end = this_beat_int + 2`.
                # TODO: no such test case is provide (in the paper or our implementation) of `end > this_beat_int + 2`.
                numerator = 1

            distance_to_nearest_beat = abs(round(onset) - Fraction(onset))
            if distance_to_nearest_beat == 0:
                per_note_syncopation_values.append(0)
                continue

            per_note_syncopation_values.append(
                Fraction(numerator, distance_to_nearest_beat)
            )

        if cycle_length is not None:
            denominator = len(onset_beats)
        else:
            denominator = len(per_note_syncopation_values) + 1

        return sum(per_note_syncopation_values) / denominator


def vector_to_onset_beat(vector: list, beat_unit_length: int = 2):
    """
    Map from a vector to onset beat data via `vector_to_multiset`.

    Examples
    --------
    >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]
    >>> vector_to_onset_beat(vector=son, beat_unit_length=4)
    (Fraction(0, 1), Fraction(3, 4), Fraction(3, 2), Fraction(5, 2), Fraction(3, 1))

    """
    onsets = [i for i, count in enumerate(vector) for _ in range(count)]
    return tuple(Fraction(x, beat_unit_length) for x in onsets)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
