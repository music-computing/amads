from typing import List, Sequence
import math

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
    def __init__(self, order: int, smoothing_factor: float = 0.1):
        self.order = order
        self.smoothing_factor = smoothing_factor
        self.reset()

    def reset(self) -> None:
        """Reset the model to its initial untrained state."""
        self.vocabulary = set()
        self.ngrams = {}

    def update(self, corpus) -> None:
        """Update the model with new data without resetting existing knowledge."""
        for sequence in corpus:
            # Convert sequence to tuple for easier handling
            seq = tuple(sequence)
            # For each possible n-gram in the sequence
            for i in range(len(seq) - self.order):
                # Get the context (previous tokens) and the target token
                context = seq[i:i + self.order]
                target = seq[i + self.order]
                
                # Initialize context in ngrams if not present
                if context not in self.ngrams:
                    self.ngrams[context] = {}
                
                # Count the frequency of the target given this context
                self.ngrams[context][target] = self.ngrams[context].get(target, 0) + 1
                self.vocabulary.add(target)

    def train(self, corpus) -> None:
        """Train the model by counting N-gram frequencies in the corpus. 
        This will reset the model to its initial untrained state before training."""
        
        self.reset()
        self.update(corpus)

    def predict_sequence(self, sequence: List[Token]) -> List[ProbabilityDistribution]:
        """Generate predictions for each token in the sequence given previous tokens."""
        predictions = []
        seq = tuple(sequence)
        
        # For each position where we can make a prediction
        for i in range(len(seq) - self.order):
            context = seq[i:i + self.order]
            target = seq[i + self.order]
            pred = self.predict_token(context, target)
            predictions.append(pred)
            
        return predictions

    def predict_token(self, context: tuple, current_token: Token) -> ProbabilityDistribution:
        """Predict probability distribution for next token given context."""
        # Add current_token to vocabulary if it's new
        self.vocabulary.add(current_token)
        V = len(self.vocabulary)  # vocabulary size
        
        if context not in self.ngrams:
            # For unseen contexts, use maximum smoothing (equivalent to uniform)
            # Every token gets the same smoothed probability
            return ProbabilityDistribution({t: 1/V for t in self.vocabulary})
            
        # Get counts and apply smoothing
        probabilities = {}
        total_count = sum(self.ngrams[context].values()) + (self.smoothing_factor * V)
        
        # Calculate smoothed probability for all possible tokens
        for token in self.vocabulary:
            count = self.ngrams[context].get(token, 0)
            probabilities[token] = (count + self.smoothing_factor) / total_count
        
        return ProbabilityDistribution(probabilities)

class IDyOMModel(ExpectationModel):
    def __init__(self, max_order: int = 8, smoothing_factor: float = 0.1, bias: float = 1.0):
        """
        Initialize IDyOM model with both long-term and short-term components.
        
        Args:
            max_order: Maximum order of Markov models to use
            smoothing_factor: Smoothing factor for probability distributions
            bias: Exponential bias parameter for entropy-based weighting.
                 - bias > 1: Sharpens the weighting, giving even more influence to the more
                   confident model (lower entropy)
                 - bias < 1: Smooths the weighting, making the models' influences more equal
                   regardless of their confidence
                 - bias = 1: Direct use of inverse normalized entropy (default)
        """
        self.max_order = max_order
        self.smoothing_factor = smoothing_factor
        self.bias = bias
        
        # Long-term models (trained on full corpus)
        self.ltm_models = [
            MarkovModel(order=i, smoothing_factor=smoothing_factor)
            for i in range(1, max_order + 1)
        ]
        
        # Short-term models (trained incrementally)
        self.stm_models = [
            MarkovModel(order=i, smoothing_factor=smoothing_factor)
            for i in range(1, max_order + 1)
        ]

    def train(self, corpus) -> None:
        """Train only the Long-Term Models (LTM) on the corpus."""
        # Train LTM models first (and build vocabulary
        for model in self.ltm_models:
            model.train(corpus)
        
        # Share the vocabulary with STM models
        full_vocab = set()
        for model in self.ltm_models:
            full_vocab.update(model.vocabulary)
        
        # Reset STM models but give them the full vocabulary
        for model in self.stm_models:
            model.reset()
            model.vocabulary = full_vocab.copy()  # Give each STM model the full vocabulary

    def _calculate_shannon_entropy(self, distribution: ProbabilityDistribution) -> float:
        """Calculate Shannon entropy E(X) of a probability distribution."""
        entropy = 0
        for _, p in distribution.distribution.items():
            entropy -= p * math.log2(p)
        return entropy
    
    def _calculate_max_entropy(self, support_size: int) -> float:
        """Calculate maximum entropy Emax(X) for given support size."""
        return math.log2(support_size)
    
    def _calculate_normalized_entropy(self, distribution: ProbabilityDistribution) -> float:
        """Calculate normalized entropy NE(X) = E(X)/Emax(X)."""
        shannon_entropy = self._calculate_shannon_entropy(distribution)
        max_entropy = self._calculate_max_entropy(len(distribution.distribution))
        return shannon_entropy / max_entropy

    def predict_token(self, context: Sequence[Token], target: Token = None) -> ProbabilityDistribution:
        """Predict the next token given a context using both LTM and STM models."""
        # Get predictions from all available orders of LTM and STM
        ltm_predictions = []
        stm_predictions = []
        
        context_len = len(context)
        for order in range(1, min(context_len + 1, self.max_order + 1)):
            model_idx = order - 1
            order_context = context[-order:]
            
            ltm_pred = self.ltm_models[model_idx].predict_token(order_context, target)
            stm_pred = self.stm_models[model_idx].predict_token(order_context, target)
            
            ltm_predictions.append(ltm_pred)
            stm_predictions.append(stm_pred)
            
        # Combine predictions using entropy weighting
        combined_ltm = self.entropy_weighted_combination(ltm_predictions)
        combined_stm = self.entropy_weighted_combination(stm_predictions)
        
        # Final combination of LTM and STM
        final_pred = self.entropy_weighted_combination([combined_ltm, combined_stm])
        return final_pred

    def entropy_weighted_combination(self, predictions: List[ProbabilityDistribution]) -> ProbabilityDistribution:
        """Combine predictions using entropy-based weighting."""
        if not predictions:
            return ProbabilityDistribution({})
            
        # Calculate entropy for each distribution
        entropies = [pred.entropy() for pred in predictions]
            
        # Convert entropies to weights (lower entropy -> higher weight)
        total_entropy = sum(entropies)
        if total_entropy == 0:
            weights = [1/len(predictions)] * len(predictions)
        else:
            weights = [1 - (e/total_entropy) for e in entropies]
            weight_sum = sum(weights)
            if weight_sum > 0:
                weights = [w/weight_sum for w in weights]
            else:
                weights = [1/len(predictions)] * len(predictions)
        
        # Combine distributions using weights
        combined = {}
        all_tokens = set()
        for pred in predictions:
            all_tokens.update(pred.distribution.keys())
            
        for token in all_tokens:
            weighted_sum = sum(pred.distribution.get(token, 0.0) * weight 
                             for pred, weight in zip(predictions, weights))
            combined[token] = weighted_sum
                
        return ProbabilityDistribution(combined)

    def predict_sequence(self, sequence: List[Token]) -> List[ProbabilityDistribution]:
        """Generate predictions for each token in the sequence given previous tokens."""
        predictions = []
        seq = tuple(sequence)
        
        # For each position where we can make a prediction (starting after first note)
        for i in range(len(seq) - 1):
            # Train STM models on the sequence seen so far
            current_sequence = seq[:i + 1]
            for model in self.stm_models:
                model.update([current_sequence])
            
            # Get context and make prediction
            context = seq[:i + 1]  # Use all available context
            target = seq[i + 1]
            pred = self.predict_token(context, target)
            predictions.append(pred)
            
        return predictions



