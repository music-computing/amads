"""
Measures of syncopation from the literature.
"""

__author__ = "Mark Gotham"

from fractions import Fraction
from typing import Optional

from partitura import load_score


class SyncopationMetric:
    def __init__(self, path_to_score: Optional[str] = None):
        """
        The methods of this class implement syncopation metrics from the literature.
        These are typically based on simple data (note start times and similar).

        The parameters of this class allow users to run from a score (with onsets etc. deduced from there)
        or directly on their own data (the necessary parameters differ slightly for each method).

        Parameters
        ----------
        path_to_score:
            Path to the score in any supported format (e.g., MusicXML).
            Deduce any necessary onsets, beats etc. from the score as calculated by Partitura.
            Warning: Partitura takes "beats" from time signatures denominators, e.g., 6/8 has 6 "beats" (not 2).
        """
        self.path_to_score = path_to_score
        self.note_array = (
            None  # TODO. TBC. May be redundant / better handled on a per-metric basis.
        )

    def load_note_array_from_score(self):
        """
        Parse a score and return Partitura's `.note_array()` with `include_metrical_position=True`.
        This should cover the required information.
        The note array's fields includes several fields of which methods here use the following (in their words):
            * 'onset_beat': onset time of the note in beats
            * 'duration_beat': duration of the note in beats
        These values are called in the form `note_array["onset_beat"]`.

        """
        if self.note_array is not None:
            print("already retrieved, skipping")
            return
        if self.path_to_score is None:
            raise ValueError("No score provided.")
        else:
            score = load_score(self.path_to_score)
            self.note_array = score.note_array(include_metrical_position=True)

    def weighted_note_to_beat_distance(
        self, onset_beats: Optional[list] = None
    ) -> float:
        """
        The weighted note-to-beat distance measure (WNBD)
        measures the distance between note starts and
        records the traversing of beats, and the distance to the nearest beat.

        The authors clarify that "notes are supposed to end where the next note starts",
        so we're working with the inter-note interval (INI), rather than the duration.
        Note that there are one fewer INI values than notes.

        Among the limitations is the incomplete definition of "beat" and the agnostic view of metre:
        "By strong beats we just mean pulses." (§3.4).

        Parameters
        ----------
        onset_beats:
            User supplied data for the onset time of each note expressed in beats. Optional.

        Returns
        -------
        WNBD value (float)

        Examples
        --------
        We use the example of the son clave
        (also available from the `meter.profiles` module),
        adpating to match presentation in the literature.

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

        >>> sm = SyncopationMetric(path_to_score="../../music/musicxml/ex1.xml")
        >>> sm.weighted_note_to_beat_distance()
        Fraction(4, 3)

        """
        if (
            onset_beats is None
        ):  # Required for user-provided, if not seek a score on the class
            if self.path_to_score is not None:
                self.load_note_array_from_score()
                onset_beats = [
                    Fraction(float(x["onset_beat"])) for x in self.note_array
                ]
                # Sic, Fraction via first: Partitura uses np.float32 and Fractions do not accept that type.
                # TODO revisit class handling of this retrieval when more algos are in
            else:
                raise ValueError("No score or user values provided.")

        per_note_syncopation_values = []

        durations = [j - i for i, j in zip(onset_beats[:-1], onset_beats[1:])]
        # Sic, although Partitura note_array provides durations, we're using INI here.

        for i in range(len(durations)):
            onset = onset_beats[i]
            if int(onset) == onset:  # starts on a beat
                per_note_syncopation_values.append(0)
            else:
                duration = durations[i]
                this_beat_int = int(onset)  # NB round down
                if onset + duration <= this_beat_int + 1:  # ends before or at e_{i+1}
                    numerator = 1
                elif onset + duration <= this_beat_int + 2:  # ends before or at e_{i+2}
                    numerator = 2
                else:  # if onset + duration > this_beat_int + 2: # ends after e_{i+2}
                    numerator = 1

                distance_to_nearest_beat = abs(
                    round(onset) - Fraction(onset)
                )  # Fraction
                per_note_syncopation_values.append(
                    Fraction(numerator, distance_to_nearest_beat)
                )

        return sum(per_note_syncopation_values) / (len(per_note_syncopation_values) + 1)


def vector_to_onset_beat(vector: list, beat_unit_length: int = 2):
    """
    Map from a vector to onset beat data via `vector_to_multiset`.

    Examples
    --------
    >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1]  # Final 1 for cycle rotation
    >>> vector_to_onset_beat(vector=son, beat_unit_length=4) # NB different beat value
    (Fraction(0, 1), Fraction(3, 4), Fraction(3, 2), Fraction(5, 2), Fraction(3, 1), Fraction(4, 1))

    """
    onsets = [i for i, count in enumerate(vector) for _ in range(count)]
    return tuple(Fraction(x, beat_unit_length) for x in onsets)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
