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

    def score_to_note_array(self):
        """
        Parse a score and return Partitura's `.note_array()` with `include_metrical_position=True`.
        This should cover the required information.
        """
        if self.note_array is not None:
            print("already retrieved, skipping")
            return
        if self.path_to_score is None:
            raise ValueError("No score provided.")
        else:
            score = load_score(self.path_to_score)
            self.note_array = score.note_array(include_metrical_position=True)

    def keith(
        self,
        onset_beats: Optional[list] = None,
        duration_beats: Optional[list] = None,
        end_beats: Optional[list] = None,
    ) -> int:
        """
        Keith records per-note syncopation values with
        0 if start and end on beat,
        1 if start off, end on,
        2 if start on, end off,
        3 if start and end off,
        and an overall value by the sum of these.

        In this implementation, user provided data (see parameters) takes precedence.
        To use user-provided data, we require onsets and one of ends or durations.
        If no user data provided, seek a score on the class.

        Parameters
        ----------
        onset_beats:
            User supplied data for the onset time of each note expressed in beats. Optional.
        duration_beats:
            User supplied data for the duration of each note expressed in beats. Optional.
        end_beats:
            User supplied data for the end of each note (onset + duration) of each note expressed in beats. Optional.

        Returns
        -------
        Keith syncopation value (int)

        Examples
        --------
        We use the example of the son clave
        (also available from the `meter.profiles` module),
        adpating to match presentation in the literature.

        >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1]  # Final 1 for cycle rotation
        >>> beat_unit_length = 2
        >>> son_rhythm_onsets = tuple(i/beat_unit_length for i, count in enumerate(son) for _ in range(count))
        >>> son_rhythm_onsets
        (0.0, 1.5, 3.0, 5.0, 6.0, 8.0)

        >>> son_onset_beats = son_rhythm_onsets[: -1]
        >>> son_ends_beats = son_rhythm_onsets[1: ]
        >>> sm = SyncopationMetric()
        >>> sm.keith(onset_beats=son_onset_beats, end_beats=son_ends_beats)
        3

        This 3 consists of one on-to-off (count 2) and one off-to-on (count 1).
        """
        if onset_beats is not None:  # Required for user-provided
            if end_beats is None:  # If no ends, then deduce from starts and durations
                if duration_beats is None:
                    raise ValueError(
                        "To use user-provided data, we require onsets and one of ends or durations."
                    )
                else:
                    end_beats = [
                        onset_beats[i] + duration_beats[i]
                        for i in range(len(onset_beats))
                    ]

        else:  # seek a score on the class
            if self.path_to_score is not None:
                self.score_to_note_array()
                onset_beats = [x["onset_beat"] for x in self.note_array]
                duration_beats = [x["duration_beat"] for x in self.note_array]
                end_beats = [
                    onset_beats[i] + duration_beats[i] for i in range(len(onset_beats))
                ]
                # TODO revisit class handling of this retrieval step when more algorithms are in
            else:
                raise ValueError("No score or user values provided.")

        per_note_syncopation_values = (
            []
        )  # TODO. Currently, in case we want to report on the sequence, not just the sum

        for i in range(len(onset_beats)):
            start = onset_beats[i]
            end = end_beats[i]

            if abs(round(start) - start) == 0:  # start on the beat ...
                if int(end) == end:  # ... and end on.
                    per_note_syncopation_values.append(0)
                else:  # ... but end off.
                    per_note_syncopation_values.append(2)
            else:  # start off the beat ...
                if int(end) == end:  # ... but end on.
                    per_note_syncopation_values.append(1)
                else:  # ... and end off
                    per_note_syncopation_values.append(3)

        return sum(per_note_syncopation_values)

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

        >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1]  # Final 1 for cycle rotation
        >>> beat_unit_length = 2
        >>> son_rhythm_onsets = tuple(i/beat_unit_length for i, count in enumerate(son) for _ in range(count))
        >>> son_rhythm_onsets
        (0.0, 1.5, 3.0, 5.0, 6.0, 8.0)

        >>> son_onset_beats = son_rhythm_onsets[: -1]
        >>> son_ends_beats = son_rhythm_onsets[1: ]
        >>> sm = SyncopationMetric()
        >>> sm.weighted_note_to_beat_distance(onset_beats=son_onset_beats)
        Fraction(1, 1)

        >>> beat_unit_length = 4
        >>> son_rhythm_onsets = tuple(i/beat_unit_length for i, count in enumerate(son) for _ in range(count))
        >>> son_rhythm_onsets
        (0.0, 0.75, 1.5, 2.5, 3.0, 4.0)

        >>> son_onset_beats = son_rhythm_onsets[: -1]
        >>> son_ends_beats = son_rhythm_onsets[1: ]
        >>> sm = SyncopationMetric()
        >>> sm.weighted_note_to_beat_distance(onset_beats=son_onset_beats)
        Fraction(7, 2)

        """
        if (
            onset_beats is None
        ):  # Required for user-provided, if not seek a score on the class
            if self.path_to_score is not None:
                self.score_to_note_array()
                onset_beats = [x["onset_beat"] for x in self.note_array]
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

                distance_to_nearest_beat = abs(round(onset) - onset)
                per_note_syncopation_values.append(
                    Fraction(numerator / distance_to_nearest_beat)
                )

        return sum(per_note_syncopation_values) / len(per_note_syncopation_values)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
