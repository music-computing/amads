"""
Melodic similarity
==================

This example demonstrates how we can calculate the similarity between two
melodies using the `melsim` module, which is a Python wrapper for the `melsim`
R package (https://github.com/sebsilas/melsim).
"""

# %%
# First, we'll import the required modules.

import numpy as np
import pandas as pd

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    check_r_packages_installed,
    get_similarity,
    r_get_similarity,
    r_load_melody,
)
from amads.utils import check_python_package_installed

# %%
# Check if all required dependencies are installed.


def test_check_dependencies():
    check_python_package_installed("rpy2")
    check_r_packages_installed(install_missing=True)


test_check_dependencies()

# %%
# Create example melodies for comparison. We'll start with a C major scale and
# create variations by altering different notes.

# Create a C major scale melody (C4 to C5) with quarter note durations
c_major_scale = Score.from_melody(
    pitches=[60, 62, 64, 65, 67, 69, 71, 72], durations=1.0
)

# Create variations by altering different notes
modified_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 71, 72], durations=1.0  # F4->F#4
)

third_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 71, 72], durations=1.0  # F4->F#4, A4->Ab4
)

fourth_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 70, 72], durations=1.0  # F4->F#4, A4->Ab4, B4->Bb4
)

melodies = [c_major_scale, modified_scale, third_scale, fourth_scale]

# %%
# Perform a simple similarity comparison between two melodies using Jaccard similarity.

get_similarity(c_major_scale, modified_scale, "Jaccard", "pitch")

# %%
# Now perform pairwise comparisons across all melodies using different similarity measures.

# Load melodies into R
for i, melody in enumerate(melodies):
    r_load_melody(melody, f"melody_{i + 1}")

similarity_measures = ["cosine", "Simpson"]

for method in similarity_measures:
    n = len(melodies)
    sim_matrix = np.zeros((n, n))
    melody_names = [f"melody_{i + 1}" for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            similarity = r_get_similarity(
                f"melody_{i + 1}", f"melody_{j + 1}", method, "pitch"
            )
            sim_matrix[i, j] = similarity
            sim_matrix[j, i] = similarity
        sim_matrix[i, i] = 1.0
    sim_df = pd.DataFrame(sim_matrix, index=melody_names, columns=melody_names)
    print(f"\nPairwise {method} similarities:")
    print(sim_df)

# %%
# Finally, explore other types of melodic similarity measures.

# Compare intervallic similarity
get_similarity(c_major_scale, modified_scale, "Euclidean", "int")

# %%
# Compare IOI class similarity (expected to be 1 as IOIs are identical)
get_similarity(c_major_scale, modified_scale, "Canberra", "ioi_class")
