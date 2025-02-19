import matplotlib.pyplot as plt
import numpy as np
import os
#This is hacky and should be fixed if/when package is properly installed
import sys
sys.path.append('./amads')

from amads.algorithms import boundary
from amads.io import partitura_midi_import, pianoroll
from amads.music import example
from amads.expectation.tokenizer import MelodyIntervalTokenizer
from amads.expectation.dataset import ScoreDataset
from amads.expectation.model import MarkovModel, IDyOMModel
from amads.expectation.metrics import NegativeLogLikelihood, Entropy
import pickle

# Get the path to the package's music directory-- to be fixed when sample datasets are properly included in the package
package_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(package_dir, '..', 'amads', 'music', 'Marion_2024_Bach_Chorales.pkl')
score_data = pickle.load(open(data_path, 'rb'))

tokenizer = MelodyIntervalTokenizer()
dataset = ScoreDataset(score_data, tokenizer)

training_sequences = dataset[0:-10].copy()
test_sequence = dataset[-7].copy()

# Create and train both models: A simple Markov model and a more complex IDyOM model
idyom = IDyOMModel(max_order=5, smoothing_factor=0.01)
markov = MarkovModel(order=5, smoothing_factor=0.01)

idyom.train(training_sequences)
markov.train(training_sequences)

# Get predictions for test sequence
idyom_predictions = idyom.predict_sequence(test_sequence)
markov_predictions = markov.predict_sequence(test_sequence)

# Create our metrics
nll_metric = NegativeLogLikelihood()
entropy_metric = Entropy()

idyom_nll = nll_metric.compute(idyom_predictions, test_sequence[1:])#sum(-log2(pred.distribution.get(actual, 1e-10)) 
               #for pred, actual in zip(idyom_predictions, test_sequence[1:])) / len(idyom_predictions)
markov_nll = nll_metric.compute(markov_predictions, test_sequence[markov.order:])#sum(-log2(pred.distribution.get(actual, 1e-10)) 
                #for pred, actual in zip(markov_predictions, test_sequence[1:])) / len(markov_predictions)

print(f"IDyOM average NLL {np.mean(idyom_nll):.2f}")
print(f"Markov average NLL {np.mean(markov_nll):.2f}")


# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8), height_ratios=[2, 1])

# Top subplot: The actual sequence (intervals)
intervals = [token.value for token in test_sequence]
ax1.plot(range(len(intervals)), intervals, 'k-', label='Melody intervals')
ax1.set_ylabel('Interval size')
ax1.grid(True)
ax1.legend()

# Bottom subplot: Surprise values using NLL metric
# IDyOM predictions
idyom_positions = range(1, len(idyom_predictions) + 1)
idyom_nll = nll_metric.compute(idyom_predictions, test_sequence[1:])
ax2.plot(idyom_positions, idyom_nll, 'b-', label='IDyOM', alpha=0.7)

# Markov predictions
markov_positions = range(markov.order, len(test_sequence))
markov_nll = nll_metric.compute(markov_predictions, test_sequence[markov.order:])
ax2.plot(markov_positions, markov_nll, 'r-', label='Markov', alpha=0.7)

ax2.set_xlabel('Position in sequence')
ax2.set_ylabel('Negative Log Likelihood')
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()

# Get predictions for the test sequence
#predictions = model.predict_sequence(test_sequence)


# Things that we want to be able to do:
#
# Compute cross-entropy for a sequence; i.e. tells us how well the model
# predicts the sequence overall.
#
# Compute note-level log probability for a sequence; i.e. tells us how well
# the model predicts each token. We expect this to correspond somewhat to the
# listener's experience of surprise.
#
# For each token, compute the entropy of the model's predictions for that token.
# That tells us about the model's uncertainty about the token.
#
## Further questions:
#
# Moment-to-moment learning - can we quantify how much the model is learning
# as it progresses through a sequence? There are some ideas that this is
# related to the reward people get from listening to music.
# To implement this, we need to think about predict_sequence; maybe it's not
# just predicting but also updating the model.
#
# from amads.expectation.metrics import cross_entropy

# score = cross_entropy(predictions, tokens)

# print(score)