"""
Jazz classification
===================

This example demonstrates how to perform a simple classification of jazz recordings
from the Jazz Trio Database using a range of features extracted with AMADS.

We'll train a simple binary classifier to identify whether a recording is by Bill Evans
or Oscar Peterson using a combination of different melodic and rhythmic features
"""

# %%
# First, we'll import the required modules.

import random

import matplotlib.pyplot as plt
import mirdata
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from amads.algorithms.complexity import lz77_complexity
from amads.io.readscore import read_score
from amads.polyphony.skyline import skyline
from amads.time.swing import beat_upbeat_ratio
from amads.time.tempo import tempo_mean, tempo_slope

# %%
# Set some constants
N_TRACKS = 10  # we'll only analyse this many tracks per performer
SEED = 42

np.random.seed(SEED)
random.seed(SEED)


# %%
# Download the Jazz Trio Database (MIDI only) using mirdata
# Note that this will only download annotations (beats, MIDI)
# and will not download the audio files directly

jtd = mirdata.initialize("jtd")
jtd.download()

# %%
# Now, we load both the tracks (single instrument data, i.e. just piano)
# and the multitracks (data for all instruments, e.g. beat tracker results)

jtd_tracks = jtd.load_tracks()
jtd_multitracks = jtd.load_multitracks()

# %%
# Print out information for a single random track
print(jtd.choice_track())

# %%
# We're going to train a simple binary classifier (logistic regression)
# to identify whether a recording is by Bill Evans or Oscar Peterson.
# First things first, we need to get all of our Evans and Peterson tracks

evansb_tracks = []
petersono_tracks = []

for mtrack_id in jtd.mtrack_ids:
    associated_multitrack = jtd_multitracks[mtrack_id]
    # We can grab the pianist data easily from the multitrack
    associated_track = associated_multitrack.piano
    # Store the track inside the list if required
    if associated_track.musician == "Bill Evans":
        evansb_tracks.append(associated_multitrack)
    elif associated_track.musician == "Oscar Peterson":
        petersono_tracks.append(associated_multitrack)
    else:
        continue

evansb_tracks = random.sample(evansb_tracks, N_TRACKS)
petersono_tracks = random.sample(petersono_tracks, N_TRACKS)


# %%
def load_track_annotations(mtrack) -> tuple:
    """Load MIDI and beat positions for a track"""
    # Get the pianist data from the multitrack
    track = mtrack.piano
    # Load the MIDI file using AMADS' current reader API.
    score = read_score(track.midi_path, show=False)
    # We'll apply the skyline to the score to get just the melody
    skylined = skyline(score)
    # MIDI scores use quarter-note units; JTD beat annotations use seconds.
    # Preserve expressive timing by converting with the MIDI tempo map.
    skylined.convert_to_seconds()
    skylined_notes = skylined.get_sorted_notes()
    # Now, we want to get the piano onset times and MIDI pitches as separate lists
    pitches = [note.midi_num for note in skylined_notes]
    onsets = [note.onset for note in skylined_notes]
    # We also want to get the output from the beat track
    # This is a list of crotchet beat timestamps
    beats = mtrack.beats.times
    return pitches, onsets, beats


evansb_read = [load_track_annotations(t) for t in evansb_tracks]
petersono_read = [load_track_annotations(t) for t in petersono_tracks]

# %%
# Extract all features from all tracks


def melody_features(pitches: list[int]):
    """Extracts melodic features from a list of (skylined) pitches"""
    # First, we'll use the normalized LZ77 complexity
    # This can be calculated as the length of the LZ77 compressed
    # sequence of pitches, vs the raw number of pitches
    lz77 = lz77_complexity(pitches, normalized=True)
    # Next, we'll extract the number of unique pitch classes and note count
    nunique = len(list({note % 12 for note in pitches}))
    ons_dens = len(pitches)
    return lz77, nunique, ons_dens


def rhythm_features(onsets: list[float], beats: list[float]):
    """Extracts rhythmic features from lists of onsets and beats"""
    # First, we'll extract the mean and standard deviation beat-upbeat ratio
    # We express BURs as base-2 log and remove outliers
    try:
        burs = beat_upbeat_ratio(beats, onsets, log2=True, bounded=True)
    # Occasionally we can encounter errors here, so set the values to NaN
    # We'll impute these using training-set feature means later on
    # Errors mostly relate to e.g., no BURs being present
    except ValueError:
        mean_bur = np.nan
        std_bur = np.nan
    else:
        # `bur_array == nan` when no BUR can be calculated for two consecutive beats
        # this is expected behaviour and ensures that `shape(burs) == shape(beats) - 1`
        bur_array = np.array(burs, dtype=float)
        valid_burs = bur_array[np.isfinite(bur_array)]
        mean_bur = np.mean(valid_burs) if valid_burs.size else np.nan
        std_bur = np.std(valid_burs) if valid_burs.size else np.nan
    # Next, we'll extract the tempo slope and mean BPM from the extracted beats
    tslope = tempo_slope(beats)
    tmean = tempo_mean(beats)
    return mean_bur, std_bur, tslope, tmean


def extract_features(track_data) -> list:
    """Extract all features for a single track"""
    # Unpack the tuple
    pitches, onsets, beats = track_data
    # Extract separate melody and rhythm features
    lz77, nunique, ons_dens = melody_features(pitches)
    mbur, sbur, tslope, tmean = rhythm_features(onsets, beats)
    # Pack into a single list and return
    return [lz77, nunique, ons_dens, mbur, sbur, tslope, tmean]


evansb_features = [extract_features(t) for t in evansb_read]
petersono_features = [extract_features(t) for t in petersono_read]

# %%
# Assemble the feature array: shape (n_tracks, n_features)
X = np.vstack([evansb_features, petersono_features])
# Assemble the target array: shape (n_tracks),
# We use a target of 0 when the pianist is Bill Evans, 1 when it is Oscar Peterson
y = np.hstack(
    [
        [0 for _ in range(len(evansb_features))],
        [1 for _ in range(len(petersono_features))],
    ]
)
# Sanity check
assert X.shape[0] == y.shape[0]

# %%
# Split into train-validation sets
# Split raw features before fitting any imputation or scaling statistics.
# We'll use a 4:1 train-validation ratio here.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    train_size=0.8,
    random_state=SEED,
    shuffle=True,
    stratify=y,  # ensures an equal number of recordings by both classes in every subset
)


# %%
# Fit the model
# We'll just use a logistic regression with L2 norm for the ease of interpretation
# but this could, in practice, be a random forest or an SVM, etc. etc.
# The pipeline fits preprocessing only on the training subset. Keep entirely
# missing columns so the seven feature names still match the coefficients.
model = make_pipeline(
    SimpleImputer(strategy="mean", keep_empty_features=True),
    StandardScaler(),
    LogisticRegression(random_state=SEED),
)
model.fit(X_train, y_train)
# Calculate the accuracy on the unseen data
acc = model.score(X_test, y_test)
print(f"Model accuracy: {(acc * 100):.2f}%")


# %%
# Visualise the model predictions
cmat = confusion_matrix(y_test, model.predict(X_test))
disp = ConfusionMatrixDisplay(
    confusion_matrix=cmat, display_labels=["Evans", "Peterson"]
)
disp.plot()
plt.show()


# %%
# Visualise the weights associated with each feature
coef_labels = [
    "Melodic complexity",
    "Unique pitches",
    "Number of pitches",
    "BUR (mean)",
    "BUR (std)",
    "Tempo slope (BPM/s)",
    "Mean tempo (BPM)",
]
# Extract the odds ratios as the exponential of the coefficients
odds_ratios = np.exp(model.named_steps["logisticregression"].coef_.flatten())

# Create the plot
fig, ax = plt.subplots()
ax.bar(coef_labels, odds_ratios)
ax.set(xlabel="Feature", ylabel="Odds ratio")
ax.tick_params(axis="x", labelrotation=90)
ax.axhline(1, 0, 1, color="black")
fig.tight_layout()
plt.show()

# %%
# Here, a feature > 1 == increases are more likely to be the "target" class (Oscar Peterson)
# Vice versa, a feature < 1 == increases are less likely to be the target class
