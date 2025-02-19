from typing import List
from amads.core.basics import Score
from amads.pitch.ismonophonic import ismonophonic
from amads.core.basics import Note
from abc import ABC, abstractmethod

class Token:
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"Token({self.value})"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)


class Tokenizer(ABC):
    @abstractmethod    
    def tokenize(self, x) -> List[Token]:
        """All tokenizer subclasses must implement this method"""
        pass

class MelodyIntervalTokenizer(Tokenizer):
    """
    Tokenize a melody as a sequence of pitch intervals, ignoring rhythm.
    """
    def tokenize(self, x) -> List[Token]:
        assert isinstance(x, Score)
        assert ismonophonic(x)

        flat_score = x.flatten(collapse=True)
        tones = list(flat_score.find_all(Note))
        tokens = []

        for prev_note, current_note in zip(tones[:-1], tones[1:]):
            interval = current_note.keynum - prev_note.keynum
            tokens.append(Token(interval))

        return tokens

class AudioTokenizer(Tokenizer):
    pass

class IOITokenizer(Tokenizer):
    """
    Tokenize a melody as a sequence of inter-onset intervals (time between note starts).
    """
    def tokenize(self, x) -> List[Token]:
        assert isinstance(x, Score)
        assert ismonophonic(x)

        flat_score = x.flatten(collapse=True)
        notes = list(flat_score.find_all(Note))
        tokens = []

        for prev_note, current_note in zip(notes[:-1], notes[1:]):
            ioi = current_note.start - prev_note.start
            tokens.append(Token(ioi))

        return tokens
