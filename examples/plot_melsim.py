"""
Melodic similarity
==================

This example demonstrates how we can calculate the similarity between two
melodies using the `melsim` module, which is a Python wrapper for the `melsim`
R package (https://github.com/sebsilas/melsim).
"""

# %%
# First, we'll import the required modules.

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    check_r_packages_installed,
    get_similarities,
    get_similarity,
)

# %%
# Check if all required dependencies are installed.


def test_check_dependencies():
    """Check if R packages are installed."""
    try:
        check_r_packages_installed(install_missing=False)
        print("All R packages are installed.")
    except ImportError:
        print(
            "Some R packages are missing. Please run install_dependencies() from the melsim module."
        )


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
    pitches=[60, 62, 64, 66, 67, 69, 71, 72], durations=1.0  # F4->F#4
)

third_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 71, 72], durations=1.0  # F4->F#4, A4->Ab4
)

fourth_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 70, 72], durations=1.0  # F4->F#4, A4->Ab4, B4->Bb4
)

melodies = {
    "c_major_scale": c_major_scale,
    "modified_scale": modified_scale,
    "third_scale": third_scale,
    "fourth_scale": fourth_scale,
}

# %%
# Perform a simple similarity comparison between two melodies using Jaccard similarity.

similarity = get_similarity(c_major_scale, modified_scale, "Jaccard", "pitch")
print(f"Jaccard similarity between c_major_scale and modified_scale: {similarity}")

# %%
# Now perform pairwise comparisons across all melodies using different similarity measures.

similarity_measures = ["cosine", "Simpson"]

for method in similarity_measures:
    # Use batch processing for efficiency
    batch_results = get_similarities(melodies, method=method, transformation="pitch")

    # batch_results is now a single matrix (since single method/transformation)
    print(f"\nPairwise {method} similarities:")

    # Display the similarity matrix
    melody_names = list(melodies.keys())

    # Print header
    print(f"{'':20}", end="")
    for name in melody_names:
        print(f"{name:15}", end="")
    print()

    # Print matrix rows
    for name1 in melody_names:
        print(f"{name1:20}", end="")
        for name2 in melody_names:
            similarity = batch_results[name1][name2]
            print(f"{similarity:15.4f}", end="")
        print()

# %%
# Finally, explore other types of melodic similarity measures.

# Compare intervallic similarity
intervallic_sim = get_similarity(c_major_scale, modified_scale, "Euclidean", "int")
print(f"\nEuclidean intervallic similarity: {intervallic_sim}")

# %%
# Compare IOI class similarity (expected to be 1 as IOIs are identical)
ioi_sim = get_similarity(c_major_scale, modified_scale, "Canberra", "ioi_class")
print(f"Canberra IOI class similarity: {ioi_sim}")

# %%
# Compare using different transformations
transformations = ["pitch", "int", "parsons", "pc"]
print("\nSimilarity across different transformations:")
for transformation in transformations:
    sim = get_similarity(c_major_scale, modified_scale, "Jaccard", transformation)
    print(f"Jaccard {transformation} similarity: {sim:.4f}")

# %%
# Comprehensive comparison using multiple methods and transformations
print("\nComprehensive comparison (multiple methods and transformations):")
comprehensive_results = get_similarities(
    {"melody1": c_major_scale, "melody2": modified_scale},
    method=["Jaccard", "Dice", "cosine", "Euclidean"],
    transformation=["pitch", "int", "parsons", "pc"],
)

# Display results in a formatted table
print(f"{'Method':12} {'Transform':15} {'Similarity':>12}")
print("-" * 40)
for (method, transformation), matrix in comprehensive_results.items():
    similarity = matrix["melody1"]["melody2"]
    print(f"{method:12} {transformation:15} {similarity:12.4f}")
