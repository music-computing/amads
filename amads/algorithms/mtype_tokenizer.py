import warnings
from collections.abc import Hashable
from typing import Dict, List, Optional, Union

from amads.core.basics import Note, Score

# collections.abc is currently not supported in Python 3.13.1


class MelodyTokenizer:
    """Base class for tokenizing melodies into n-grams.

    Attributes
    ----------
    precision : int
        Number of decimal places to round IOI values to
    phrases : list
        List of melody phrases after segmentation
    """

    def __init__(self):
        self.precision = 6
        self.phrases = []

    def tokenize_melody(self, score: Score) -> List[List]:
        """Tokenize a melody into phrases.

        Parameters
        ----------
        score : Score
            A Score object containing a melody

        Returns
        -------
        list[list]
            List of tokenized phrases
        """
        notes = self.get_notes(score)
        self.phrases = self.segment_melody(notes)
        return [self.tokenize_phrase(phrase) for phrase in self.phrases]

    def get_notes(self, score: Score) -> List[Note]:
        """Extract notes from score and calculate IOI values.

        Parameters
        ----------
        score : Score
            Score object to extract notes from

        Returns
        -------
        list[Note]
            List of notes with IOI and IOI ratio values calculated
        """
        flattened_score = score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))

        # Calculate IOIs and IOI ratios
        for i, note in enumerate(notes):
            if i < len(notes) - 1:
                note.ioi = round(notes[i + 1].start - note.start, self.precision)
            else:
                note.ioi = None

            if i == 0:
                note.ioi_ratio = None
            else:
                prev_ioi = notes[i - 1].ioi
                ioi = note.ioi
                if ioi is None or prev_ioi is None:
                    note.ioi_ratio = None
                else:
                    note.ioi_ratio = round(ioi / prev_ioi, self.precision)

        return notes

    def segment_melody(self, notes: List[Note]) -> List[List]:
        """Segment melody into phrases.

        Parameters
        ----------
        notes : list[Note]
            List of notes to segment

        Returns
        -------
        list[list]
            List of note phrases
        """
        raise NotImplementedError

    def tokenize_phrase(self, phrase: List[Note]) -> List:
        """Tokenize a phrase into a list of tokens.

        Parameters
        ----------
        phrase : list[Note]
            Phrase to tokenize

        Returns
        -------
        list
            List of tokens
        """
        raise NotImplementedError

    def ngram_counts(self, method: Union[str, int]) -> Dict:
        """Count n-grams in all phrases.

        Parameters
        ----------
        method : str or int
            If "all", count n-grams of all lengths.
            If int, count n-grams of that specific length.

        Returns
        -------
        dict
            Counts of each n-gram
        """
        counts = {}
        for i, phrase in enumerate(self.phrases):
            tokens = self.tokenize_phrase(phrase)
            if not tokens:
                warnings.warn(
                    f"Empty token sequence found - skipping n-gram counting for "
                    f"phrase {i + 1}\n"
                )
                continue
            if method == "all":
                # Count n-grams of all possible lengths
                for n in range(1, len(tokens) + 1):
                    for i in range(len(tokens) - n + 1):
                        ngram = tuple(tokens[i : i + n])
                        counts[ngram] = counts.get(ngram, 0) + 1
            else:
                # Count n-grams of specific length
                n = method
                if n > len(tokens):
                    raise ValueError(
                        f"n-gram length {n} is larger than token sequence length "
                        f"{len(tokens)}"
                    )
                if n < 1:
                    raise ValueError(f"n-gram length {n} is less than 1")
                for i in range(len(tokens) - n + 1):
                    ngram = tuple(tokens[i : i + n])
                    counts[ngram] = counts.get(ngram, 0) + 1
        return counts


class FantasticTokenizer(MelodyTokenizer):
    """This tokenizer produces the M-Types as defined in the FANTASTIC toolbox [1].

    An M-Type is a sequence of musical symbols (pitch intervals and duration ratios)
    that represents a melodic fragment, similar to how an n-gram represents a sequence
    of n consecutive items from a text. The length of an M-Type can vary, just like
    n-grams can be of different lengths (bigrams, trigrams, etc.)

    The tokenizer takes a score as the input, and returns a dictionary of unique
    M-Type (n-gram) counts. The top level function `get_mtype_counts()` is best for
    most users, though the other functions defined in the class are available for
    more specific use cases.

    Parameters
    ----------
    phrase_gap : float, optional
        Time gap in seconds that defines phrase boundaries, by default 1.0

    Attributes
    ----------
    phrase_gap : float
        Time gap in seconds that defines phrase boundaries
    tokens : list
        List of tokens after tokenization

    References
    ----------
    [1] Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology Accessing
        STatistics (In a Corpus): Technical Report v1.5
    """

    def __init__(self, phrase_gap: float = 1.0):
        super().__init__()
        self.phrase_gap = phrase_gap
        self.tokens = []

    def get_mtype_counts(self, score: Score, method: Union[str, int] = "all") -> Dict:
        """Get counts of M-Type n-grams in a score. This top level function takes a
        score as the input, and returns a dictionary of unique M-Type (n-gram)
        counts.

        First segments melody into phrases, then tokenizes each phrase into pitch
        interval and IOI ratio classes. Finally counts unique n-grams.

        The method argument is used to specify the length of the n-grams to count.
        If "all", all n-grams of all lengths are counted. If an integer, only
        n-grams of that specific length are counted.

        Parameters
        ----------
        score : Score
            Score object containing melody
        method : str or int, optional
            If "all", count n-grams of all lengths.
            If int, count n-grams of that specific length, by default "all"

        Returns
        -------
        dict
            Counts of each unique n-gram
        """
        self.tokenize_melody(score)
        return self.ngram_counts(method)

    def tokenize_melody(self, score: Score) -> List[List]:
        """Tokenize melody into M-Types.

        Parameters
        ----------
        score : Score
            Score object to tokenize

        Returns
        -------
        list[list]
            List of tokenized phrases
        """
        notes = self.get_notes(score)
        self.phrases = self.segment_melody(notes)
        self.tokens = [self.tokenize_phrase(phrase) for phrase in self.phrases]
        return self.tokens

    def segment_melody(self, notes: List[Note]) -> List[List]:
        """Segment melody into phrases based on IOI gaps.

        Parameters
        ----------
        notes : list[Note]
            List of notes to segment

        Returns
        -------
        list[list]
            List of note phrases
        """
        phrases = []
        current_phrase = []

        for note in notes:
            # Check whether we need to make a new phrase
            need_new_phrase = (
                len(current_phrase) > 0
                and current_phrase[-1].ioi is not None
                and current_phrase[-1].ioi > self.phrase_gap
            )
            if need_new_phrase:
                phrases.append(current_phrase)
                current_phrase = []
            current_phrase.append(note)

        if current_phrase:
            phrases.append(current_phrase)

        return phrases

    def tokenize_phrase(self, phrase: List[Note]) -> List:
        """Tokenize a phrase into M-Types.

        Parameters
        ----------
        phrase : list[Note]
            Phrase to tokenize

        Returns
        -------
        list
            List of M-Type tokens
        """
        tokens = []

        # Skip if phrase is too short
        if len(phrase) < 2:
            return tokens

        for prev_note, current_note in zip(phrase[:-1], phrase[1:]):
            pitch_interval = current_note.keynum - prev_note.keynum
            ioi_ratio = current_note.ioi_ratio

            pitch_interval_class = self.classify_pitch_interval(pitch_interval)
            ioi_ratio_class = self.classify_ioi_ratio(ioi_ratio)

            token = (pitch_interval_class, ioi_ratio_class)
            tokens.append(token)

        return tokens

    def classify_pitch_interval(self, pitch_interval: Optional[int]) -> Hashable:
        """Classify pitch interval according to Fantastic's interval class scheme.

        Parameters
        ----------
        pitch_interval : int or None
            Interval in semitones between consecutive notes

        Returns
        -------
        str or None
            Interval class label (e.g. 'd8', 'd7', 'u2', etc.)
            'd' = downward interval
            'u' = upward interval
            's' = same pitch
            't' = tritone
            Returns None if input is None
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
        ioi_ratio : float or None
            Inter-onset interval ratio between consecutive notes

        Returns
        -------
        str or None
            'q' for quicker (<0.8119)
            'e' for equal (0.8119-1.4946)
            'l' for longer (>1.4946)
            Returns None if input is None
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
        """Count n-grams in a sequence.

        Parameters
        ----------
        sequence : list[Hashable]
            Sequence to count n-grams in
        n : int
            Length of n-grams to count
        existing : dict, optional
            Existing counts to add to, by default None

        Returns
        -------
        dict
            Counts of each n-gram
        """
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
