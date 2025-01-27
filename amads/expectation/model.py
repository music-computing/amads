from typing import List

from amads.expectation.probability import ProbabilityDistribution
from amads.expectation.tokenizer import Token


class ExpectationModel:
    def train(self, corpus) -> None:
        """
        Train the model on a corpus of music.

        A corpus is a collection of musical sequences.
        """
        raise NotImplementedError

    def predict_sequence(self, sequence) -> None:
        """
        Generate predictions for a musical sequence (e.g. a melody).


        The model predicts one musical sequence at a time.
        """
        # Probably calls predict_token many times?
        raise NotImplementedError

    def predict_token(self, token):
        raise NotImplementedError


class MarkovModel(ExpectationModel):
    def __init__(self, order: int):
        self.order = order

    def train(self, corpus) -> None:
        self.ngrams = {}
        for sequence in corpus:
            raise NotImplementedError

    def predict_sequence(self, sequence: List[Token]) -> List[ProbabilityDistribution]:
        for previous_token, current_token in zip(sequence[:-1], sequence[1:]):
            self.predict_token(previous_token, current_token)

    def predict_token(self, previous_token: Token, current_token: Token) -> ProbabilityDistribution:
        raise NotImplementedError



