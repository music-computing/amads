"""
Example usage of the melsim module.
"""

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    check_r_packages_installed,
    get_similarity,
    r_get_similarity,
    r_load_melody,
)
from amads.utils import check_python_package_installed


def test_check_dependencies():
    check_python_package_installed("rpy2")
    check_r_packages_installed(install_missing=True)


test_check_dependencies()

# Create a C major scale melody as (pitch, duration) tuples
# Using MIDI note numbers: C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72

c_major_scale = Score.from_melody(
    pitches=[60, 62, 64, 65, 67, 69, 71, 72], durations=1.0  # C4 to C5  # quarter notes
)

# Create a second melody with an altered fourth note (F4->F#4)
modified_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 71, 72], durations=1.0  # C4 to C5  # quarter notes
)

# Create a third melody with two altered notes (F4->F#4 and A4->Ab4)
third_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 71, 72], durations=1.0  # C4 to C5  # quarter notes
)

# Create a fourth melody with three altered notes (F4->F#4, A4->Ab4, and B4->Bb4)
fourth_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 70, 72], durations=1.0  # C4 to C5  # quarter notes
)

melodies = [c_major_scale, modified_scale, third_scale, fourth_scale]

# Example usage - Simple similarity comparison between two melodies

similarity = get_similarity(c_major_scale, modified_scale, "Jaccard", "pitch")
print(f"Jaccard similarity between c_major_scale and modified_scale: {similarity}")
print("\n")

# Example usage - Similarity comparison across four melodies, using r_get_similarity
# Perform pairwise comparisons using 'cosine' and 'Simpson' similarity measures

# Load melodies into R
for i, melody in enumerate(melodies):
    r_load_melody(melody, f"melody_{i + 1}")

# Define measures to compare
similarity_measures = ["cosine", "Simpson"]

# Perform pairwise comparisons using the defined similarity measures
for method in similarity_measures:
    print(f"Pairwise {method} similarities:")
    for i in range(len(melodies)):
        for j in range(i + 1, len(melodies)):
            similarity = r_get_similarity(
                f"melody_{i + 1}", f"melody_{j + 1}", method, "pitch"
            )
            print(f"Similarity between melody_{i + 1} and melody_{j + 1}: {similarity}")
    print("\n")

# Example usage for a series of other transformations
intervallic_similarity = get_similarity(
    c_major_scale, modified_scale, "Euclidean", "int"
)
print(
    f"Euclidean similarity between intervals of c_major_scale and modified_scale: {intervallic_similarity}"
)

# In this example, we expect similarity to be 1, as the IOIs are identical
ioi_class_similarity = get_similarity(
    c_major_scale, modified_scale, "Canberra", "ioi_class"
)
print(
    f"Canberra similarity between ioi classes of c_major_scale and modified_scale: {ioi_class_similarity}"
)
