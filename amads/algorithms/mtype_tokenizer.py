from collections.abc import (  # collections.abc currently not supported in Python 3.13.1
    Hashable,
)
from typing import Dict, List, Optional

from amads.core.basics import Note, Score


class MelodyTokenizer:
    """Base class for tokenizing melodies into n-grams."""

    def __init__(self):
        self.precision = 6
        self.phrases = []

    def tokenize_melody(self, score: Score) -> List[List]:
        """
        Parameters
        ----------
        score : Score
            A Score object containing a melody

        Returns
        -------
        List[List]
            List of tokenized phrases
        """
        notes, iois, ioi_ratios = self.get_notes(score)
        self.phrases = self.segment_melody(notes, iois, ioi_ratios)
        return [self.tokenize_phrase(phrase, ioi_ratios) for phrase in self.phrases]

    def get_notes(self, score: Score) -> List[Note]:
        flattened_score = score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))

        onsets = [note.start for note in notes]

        iois = []
        ioi_ratios = []
        for i, onset in enumerate(onsets):
            if i < len(onsets) - 1:
                ioi = round(onsets[i + 1] - onset, self.precision)
            else:
                ioi = None
            iois.append(ioi)

        for i in range(len(onsets)):
            if i == 0:
                ioi_ratio = None
            else:
                ioi = iois[i]
                prev_ioi = iois[i - 1]
                if ioi is None or prev_ioi is None:
                    ioi_ratio = None
                else:
                    ioi_ratio = round(ioi / prev_ioi, self.precision)
            ioi_ratios.append(ioi_ratio)

        return notes, iois, ioi_ratios

    def segment_melody(
        self, notes: List[Note], iois: List[float], ioi_ratios: List[float]
    ) -> List[List]:
        raise NotImplementedError

    def tokenize_phrase(self, phrase: List[Note], ioi_ratios: List[float]) -> List:
        raise NotImplementedError

    def ngram_counts(self, n: int, ioi_ratios: List[float]) -> Dict:
        """Count n-grams in all phrases.

        Parameters
        ----------
        n : int
            Length of n-grams to count

        Returns
        -------
        Dict
            Counts of each n-gram
        """
        counts = {}
        for phrase in self.phrases:
            tokens = self.tokenize_phrase(phrase, ioi_ratios)
            for i in range(len(tokens) - n + 1):
                ngram = tuple(tokens[i : i + n])
                counts[ngram] = counts.get(ngram, 0) + 1
        return counts


class FantasticTokenizer(MelodyTokenizer):
    def __init__(self, phrase_gap: float = 1.0):
        super().__init__()
        self.phrase_gap = phrase_gap
        self.tokens = []

    def tokenize_melody(self, score: Score) -> List[List]:
        self.tokens = super().tokenize_melody(score)
        return self.tokens

    def segment_melody(
        self, notes: List[Note], iois: List[float], ioi_ratios: List[float]
    ) -> List[List]:
        phrases = []
        current_phrase = []

        for note in zip(notes, iois, ioi_ratios):
            # Check whether we need to make a new phrase
            need_new_phrase = (
                len(current_phrase) > 0
                and iois[len(current_phrase) - 1] > self.phrase_gap
            )
            if need_new_phrase:
                phrases.append(current_phrase)
                current_phrase = []
            current_phrase.append(note)

        if current_phrase:
            phrases.append(current_phrase)

        return phrases

    def tokenize_phrase(self, phrase: List[Note], ioi_ratios: List[float]) -> List:
        tokens = []

        for i, (prev_note, current_note) in enumerate(zip(phrase[:-1], phrase[1:])):
            pitch_interval = current_note.keynum - prev_note.keynum
            ioi_ratio = ioi_ratios[i]

            pitch_interval_class = self.classify_pitch_interval(pitch_interval)
            ioi_ratio_class = self.classify_ioi_ratio(ioi_ratio)

            token = (pitch_interval_class, ioi_ratio_class)
            tokens.append(token)

        return tokens

    def classify_pitch_interval(self, pitch_interval: Optional[int]) -> Hashable:
        """Classify pitch interval according to Fantastic's interval class scheme.

        Parameters
        ----------
        pitch_interval : int
            Interval in semitones between consecutive notes

        Returns
        -------
        str
            Interval class label (e.g. 'd8', 'd7', 'u2', etc.)
            'd' = downward interval
            'u' = upward interval
            's' = same pitch
            't' = tritone
        """
        # Clamp interval to [-12, 12] semitone range
        if pitch_interval is None:
            return None

        if pitch_interval < -12:
            pitch_interval = -12
        elif pitch_interval > 12:
            pitch_interval = 12

        # Map intervals to class labels based on Fantastic's scheme
        return self.interval_map[pitch_interval]

    interval_map = {
        -12: "d8",  # Descending octave
        -11: "d7",  # Descending major seventh
        -10: "d7",  # Descending minor seventh
        -9: "d6",  # Descending major sixth
        -8: "d6",  # Descending minor sixth
        -7: "d5",  # Descending perfect fifth
        -6: "dt",  # Descending tritone
        -5: "d4",  # Descending perfect fourth
        -4: "d3",  # Descending major third
        -3: "d3",  # Descending minor third
        -2: "d2",  # Descending major second
        -1: "d2",  # Descending minor second
        0: "s1",  # Unison
        1: "u2",  # Ascending minor second
        2: "u2",  # Ascending major second
        3: "u3",  # Ascending minor third
        4: "u3",  # Ascending major third
        5: "u4",  # Ascending perfect fourth
        6: "ut",  # Ascending tritone
        7: "u5",  # Ascending perfect fifth
        8: "u6",  # Ascending minor sixth
        9: "u6",  # Ascending major sixth
        10: "u7",  # Ascending minor seventh
        11: "u7",  # Ascending major seventh
        12: "u8",  # Ascending octave
    }

    def classify_ioi_ratio(self, ioi_ratio: Optional[float]) -> str:
        """Classify an IOI ratio into relative rhythm classes.

        Parameters
        ----------
        ioi_ratio : float
            Inter-onset interval ratio between consecutive notes

        Returns
        -------
        str
            'q' for quicker (<0.8119)
            'e' for equal (0.8119-1.4946)
            'l' for longer (>1.4946)
        """
        if ioi_ratio is None:
            return None
        elif ioi_ratio < 0.8118987:
            return "q"
        elif ioi_ratio < 1.4945858:
            return "e"
        else:
            return "l"

    def count_grams(
        self, sequence: List[Hashable], n: int, existing: Optional[Dict] = None
    ) -> Dict:

        # Count n-grams in a sequence
        if existing is None:
            existing = {}

        for i in range(len(sequence) - n + 1):
            # Convert sequence slice to tuple to ensure hashability
            ngram = tuple(
                tuple(x) if isinstance(x, list) else x for x in sequence[i : i + n]
            )
            existing[ngram] = existing.get(ngram, 0) + 1

        return existing
