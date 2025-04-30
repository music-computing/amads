from collections import OrderedDict
from collections.abc import Hashable
from typing import List, Optional

from amads.core.basics import Note, Score
from amads.pitch.ismonophonic import ismonophonic


class MelodyTokenizer:
    """Base class for tokenizing melodies into n-grams."""

    def __init__(self):
        """Initialize the tokenizer."""
        self.ioi_data = {}  # Dictionary to store IOI information for notes

    def tokenize(self, score: Score) -> List[List]:
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
        raise NotImplementedError

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
        # First check if score is monophonic
        if not ismonophonic(score):
            raise ValueError("Score must be monophonic")

        flattened_score = score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))

        # Clear any previous IOI data
        self.ioi_data = {}

        # Calculate IOIs and IOI ratios
        # n.b. when #68 is merged, this should be revised
        # Calculate IOIs
        for i, note in enumerate(notes):
            # Initialize entry for this note
            self.ioi_data[note] = {"ioi": None, "ioi_ratio": None}

            if i > 0:
                self.ioi_data[note]["ioi"] = note.onset - notes[i - 1].onset
            else:
                self.ioi_data[note]["ioi"] = None

            if i == 0:
                self.ioi_data[note]["ioi_ratio"] = None
            else:
                prev_note = notes[i - 1]
                prev_ioi = self.ioi_data[prev_note]["ioi"]
                ioi = self.ioi_data[note]["ioi"]
                if ioi is None or prev_ioi is None:
                    self.ioi_data[note]["ioi_ratio"] = None
                else:
                    self.ioi_data[note]["ioi_ratio"] = ioi / prev_ioi

        return notes


class FantasticTokenizer(MelodyTokenizer):
    """This tokenizer produces the M-Types as defined in the FANTASTIC toolbox [1].

    An M-Type is a sequence of musical symbols (pitch intervals and duration ratios)
    that represents a melodic fragment, similar to how an n-gram represents a sequence
    of n consecutive items from a text. The length of an M-Type can vary, just like
    n-grams can be of different lengths (bigrams, trigrams, etc.)

    The tokenizer takes a score as the input, and returns a dictionary of unique
    M-Type (n-gram) counts.

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

    def __init__(self):
        super().__init__()
        self.tokens = []

    def tokenize(self, score: Score) -> List:
        """Tokenize a melody into M-Types.

        Parameters
        ----------
        score : Score
            Score object containing melody to tokenize

        Returns
        -------
        list
            List of M-Type tokens
        """
        # Extract notes and calculate IOIs using get_notes
        notes = self.get_notes(score)
        tokens = []

        # Skip if phrase is too short
        if len(notes) < 2:
            return tokens

        for prev_note, current_note in zip(notes[:-1], notes[1:]):
            pitch_interval = current_note.num - prev_note.num
            if (
                self.ioi_data[prev_note]["ioi"] is None
                or self.ioi_data[current_note]["ioi"] is None
            ):
                ioi_ratio = None
            else:
                ioi_ratio = (
                    self.ioi_data[current_note]["ioi"] / self.ioi_data[prev_note]["ioi"]
                )

            pitch_interval_class = self.classify_pitch_interval(pitch_interval)
            ioi_ratio_class = self.classify_ioi_ratio(ioi_ratio)

            token = MType(pitch_interval_class, ioi_ratio_class)
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

    interval_map = OrderedDict(
        [
            (None, None),  # missing interval
            (-12, "d8"),  # Descending octave
            (-11, "d7"),  # Descending major seventh
            (-10, "d7"),  # Descending minor seventh
            (-9, "d6"),  # Descending major sixth
            (-8, "d6"),  # Descending minor sixth
            (-7, "d5"),  # Descending perfect fifth
            (-6, "dt"),  # Descending tritone
            (-5, "d4"),  # Descending perfect fourth
            (-4, "d3"),  # Descending major third
            (-3, "d3"),  # Descending minor third
            (-2, "d2"),  # Descending major second
            (-1, "d2"),  # Descending minor second
            (0, "s1"),  # Unison
            (1, "u2"),  # Ascending minor second
            (2, "u2"),  # Ascending major second
            (3, "u3"),  # Ascending minor third
            (4, "u3"),  # Ascending major third
            (5, "u4"),  # Ascending perfect fourth
            (6, "ut"),  # Ascending tritone
            (7, "u5"),  # Ascending perfect fifth
            (8, "u6"),  # Ascending minor sixth
            (9, "u6"),  # Ascending major sixth
            (10, "u7"),  # Ascending minor seventh
            (11, "u7"),  # Ascending major seventh
            (12, "u8"),  # Ascending octave
        ]
    )

    interval_classes = OrderedDict.fromkeys(interval_map.values())

    interval_class_codes = {
        string: integer for integer, string in enumerate(interval_classes.keys())
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

    ioi_ratio_classes = [None, "q", "e", "l"]
    ioi_ratio_class_codes = {
        None: 0,
        "q": 1,
        "e": 2,
        "l": 3,
    }


class MType:
    """A class for representing M-Types."""

    def __init__(
        self,
        pitch_interval_class: Optional[str],
        ioi_ratio_class: Optional[str],
    ):
        self.pitch_interval_class = pitch_interval_class
        self.ioi_ratio_class = ioi_ratio_class
        self.integer = self.encode()

    def encode(self) -> int:
        n_ioi_ratio_classes = len(FantasticTokenizer.ioi_ratio_classes)

        interval_class_code = FantasticTokenizer.interval_class_codes[
            self.pitch_interval_class
        ]
        ioi_ratio_class_code = FantasticTokenizer.ioi_ratio_class_codes[
            self.ioi_ratio_class
        ]

        # interval_class_code = 0, ioi_ratio_class_code = 0 -> 0
        # interval_class_code = 0, ioi_ratio_class_code = 1 -> 1
        # interval_class_code = 0, ioi_ratio_class_code = 2 -> 2
        # interval_class_code = 0, ioi_ratio_class_code = 3 -> 3
        # interval_class_code = 1, ioi_ratio_class_code = 0 -> 4
        # interval_class_code = 1, ioi_ratio_class_code = 1 -> 5
        # interval_class_code = 1, ioi_ratio_class_code = 2 -> 6
        # interval_class_code = 1, ioi_ratio_class_code = 3 -> 7
        # interval_class_code = 2, ioi_ratio_class_code = 0 -> 8
        # interval_class_code = 2, ioi_ratio_class_code = 1 -> 9
        # interval_class_code = 2, ioi_ratio_class_code = 2 -> 10
        # interval_class_code = 2, ioi_ratio_class_code = 3 -> 11
        return interval_class_code * n_ioi_ratio_classes + ioi_ratio_class_code

    def __hash__(self):
        """Return the hash based on the integer attribute."""
        return hash(self.integer)

    def __eq__(self, other):
        """Check equality based on the integer attribute."""
        if isinstance(other, MType):
            return self.integer == other.integer
        return False

    def __repr__(self):
        """Return a string representation of the MType."""
        return f"MType {self.integer}"
