from typing import List, Optional
from amads.expectation.probability import ProbabilityDistribution
from amads.expectation.tokenizer import Token
from amads.expectation.metrics import NegativeLogLikelihood, Entropy

class Prediction:
    """
    Represents a single prediction and its corresponding observation (if available).
    """
    def __init__(self, prediction: ProbabilityDistribution, observation: Optional[Token] = None):
        self.prediction = prediction
        self.observation = observation
        
        # Initialize metric calculators
        self._nll = NegativeLogLikelihood()
        self._entropy = Entropy()

    def __getitem__(self, key):
        """Allow direct access to prediction probabilities."""
        return self.prediction[key]
        
    @property
    def nll(self) -> Optional[float]:
        """Calculate negative log likelihood of the observation."""
        if self.observation is None:
            return None
        return self._nll.compute(self.prediction, self.observation)
        
    @property
    def entropy(self) -> float:
        """Calculate entropy of the prediction distribution."""
        return self._entropy.compute(self.prediction, None)


class SequencePrediction:
    """
    Represents predictions for an entire sequence.
    Behaves like a list of Predictions for compatibility.
    """
    def __init__(self, predictions: List[Prediction]):
        self.predictions = predictions
        
    def __getitem__(self, idx):
        """Allow direct indexing into predictions."""
        return self.predictions[idx]
        
    def __len__(self):
        return len(self.predictions)
        
    @property
    def observations(self) -> List[Token]:
        """Get the observed tokens that were predicted."""
        return [p.observation for p in self.predictions]
        
    @property
    def nlls(self) -> List[Optional[float]]:
        """Get negative log likelihoods for all predictions."""
        return [p.nll for p in self.predictions]
        
    @property
    def entropies(self) -> List[float]:
        """Get entropies for all predictions."""
        return [p.entropy for p in self.predictions]
        
    @property
    def mean_nll(self) -> Optional[float]:
        """Calculate mean negative log likelihood across sequence."""
        nlls = [nll for nll in self.nlls if nll is not None]
        return sum(nlls) / len(nlls) if nlls else None
        
    @property
    def mean_entropy(self) -> float:
        """Calculate mean entropy across sequence."""
        return sum(self.entropies) / len(self.entropies) 