from typing import List, Union, Optional
import math
from amads.expectation.probability import ProbabilityDistribution
from amads.expectation.tokenizer import Token

class PredictionMetric:
    """Base class for all prediction-based metrics"""
    
    def compute(self, distribution: Union[ProbabilityDistribution, List[ProbabilityDistribution]], 
                token: Union[Token, List[Token], None] = None) -> Union[float, List[float]]:
        """
        Compute metric for token(s) given distribution(s).
        
        Args:
            distribution: Single distribution or list of distributions
            token: Single token, list of tokens, or None (for metrics that don't need tokens)
            
        Returns:
            float if single token/distribution, List[float] if multiple distributions
        """
        # Handle the case where the metric doesn't require tokens (like Entropy)
        if token is None:
            if isinstance(distribution, list):
                return [self._compute_single(d, None) for d in distribution]
            return self._compute_single(distribution, None)
        
        # Handle single token case
        if isinstance(token, Token):
            return self._compute_single(distribution, token)
        
        # Handle list of tokens case
        if len(distribution) != len(token):
            raise ValueError("Must have same number of distributions and tokens")
        return [self._compute_single(d, t) 
               for d, t in zip(distribution, token)]
    
    def _compute_single(self, distribution: ProbabilityDistribution, 
                       token: Optional[Token] = None) -> float:
        """Compute metric for a single token"""
        raise NotImplementedError

class NegativeLogLikelihood(PredictionMetric):
    """
    Negative log likelihood (-log p) for each event.
    Higher values indicate more surprising events.
    """
    
    def _compute_single(self, distribution: ProbabilityDistribution, 
                       token: Token) -> float:
        prob = distribution[token]
        return -math.log2(prob)  # using log base 2 for information theory interpretation

class InformationContent(PredictionMetric):
    """
    Information content (IC) in bits.
    Identical to NLL but emphasizes information theory interpretation.
    """
    def _compute_single(self, distribution: ProbabilityDistribution, 
                       token: Token) -> float:
        return -math.log2(distribution[token])

class Entropy(PredictionMetric):
    """
    Shannon entropy of the predicted distribution.
    Measures uncertainty in the model's predictions.
    """
    def _compute_single(self, distribution: ProbabilityDistribution, 
                       token: Optional[Token] = None) -> float:
        entropy = 0
        for t, p in distribution.distribution.items():
            entropy -= p * math.log2(p)
        return entropy
