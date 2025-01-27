from typing import List
from amads.core.basics import Score
from amads.pitch import ismonophonic
from amads.expectation.token import Token


class Token:
    def __init__(self, value: int):
        self.value = value


class Tokenizer:
    def tokenize(self, x) -> List[Token]:
        raise NotImplementedError


class MelodyIntervalTokenizer(Tokenizer):
    """
    Tokenize a melody as a sequence of pitch intervals, ignoring rhythm.
    """
    def tokenize(self, x) -> List[Token]:
        assert isinstance(x, Score)
        assert ismonophonic(x)

        tokens = []

        for prev_note, current_note in zip(x.notes[:-1], x.notes[1:]):
            interval = current_note.keynum - prev_note.keynum
            tokens.append(Token(interval))

        return tokens



class AudioTokenizer(Tokenizer):
    pass
