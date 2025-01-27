from amads.algorithms import boundary
from amads.io import partitura_midi_import, pianoroll
from amads.music import example


# Actually we would need to do this for a corpus of melodies.
my_midi_file = example.fullpath("midi/melody.mid")

# Beware, partitura_midi_import is slow currently, this will be fixed soon
myscore = partitura_midi_import(my_midi_file, ptprint=False)

tokenizer = MelodyIntervalTokenizer()

tokens = tokenizer.tokenize(myscore)

model = MarkovModel(order=1)
model.train(tokens)

predictions = model.predict_sequence(tokens)


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
from amads.expectation.metrics import cross_entropy

score = cross_entropy(predictions, tokens)

print(score)