"""
Example usage of the melsim module.
"""

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    check_r_packages_installed,
    get_similarity_batch,
    get_similarity_from_scores,
    install_dependencies,
)


def test_check_dependencies():
    """Check and install dependencies if needed."""
    try:
        check_r_packages_installed(install_missing=False)
        print("All R packages are already installed.")
    except ImportError:
        print("Installing missing R packages...")
        install_dependencies()


test_check_dependencies()

# Create a C major scale melody as (pitch, duration) tuples
# Using MIDI note numbers: C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72

c_major_scale = Score.from_melody(
    pitches=[60, 62, 64, 65, 67, 69, 71, 72], durations=1.0  # C4 to C5  # quarter notes
)

# Create a second melody with an altered fourth note (F4->F#4)
modified_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 69, 71, 72],
    durations=1.0,  # C4 to C5 with F#4  # quarter notes
)

# Create a third melody with two altered notes (F4->F#4 and A4->Ab4)
third_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 71, 72],
    durations=1.0,  # C4 to C5 with F#4, Ab4  # quarter notes
)

# Create a fourth melody with three altered notes (F4->F#4, A4->Ab4, and B4->Bb4)
fourth_scale = Score.from_melody(
    pitches=[60, 62, 64, 66, 67, 68, 70, 72],
    durations=1.0,  # C4 to C5 with F#4, Ab4, Bb4  # quarter notes
)

melodies = {
    "c_major_scale": c_major_scale,
    "modified_scale": modified_scale,
    "third_scale": third_scale,
    "fourth_scale": fourth_scale,
}

# Example usage - Simple similarity comparison between two melodies

similarity = get_similarity_from_scores(
    c_major_scale, modified_scale, "Jaccard", "pitch"
)
print(f"Jaccard similarity between c_major_scale and modified_scale: {similarity}")
print()

# Example usage - Batch similarity comparison across four melodies
# Perform pairwise comparisons using 'cosine' and 'Simpson' similarity measures

print("Computing pairwise similarities using batch processing...")
batch_results = get_similarity_batch(
    melodies, method=["cosine", "Simpson"], transformation="pitch"
)

# Display results organized by similarity measure
for method in ["cosine", "Simpson"]:
    print(f"\nPairwise {method} similarities:")
    for (name1, name2, sim_method, transformation), similarity in batch_results.items():
        if sim_method == method:
            print(f"Similarity between {name1} and {name2}: {similarity:.4f}")

# Example usage for different transformations
print("\n" + "=" * 50)
print("Testing different transformations:")
print("=" * 50)

# Intervallic similarity - should be different since we changed notes
intervallic_similarity = get_similarity_from_scores(
    c_major_scale, modified_scale, "Euclidean", "int"
)
print(f"Euclidean similarity between intervals: {intervallic_similarity:.4f}")

# IOI class similarity - should be 1.0 since all durations are the same
ioi_class_similarity = get_similarity_from_scores(
    c_major_scale, modified_scale, "Jaccard", "ioi_class"
)
print(f"Jaccard similarity between IOI classes: {ioi_class_similarity:.4f}")

# Parsons code similarity - compares up/down patterns
parsons_similarity = get_similarity_from_scores(
    c_major_scale, modified_scale, "Jaccard", "parsons"
)
print(f"Jaccard similarity between Parsons codes: {parsons_similarity:.4f}")

# Pitch class similarity - ignores octaves
pc_similarity = get_similarity_from_scores(
    c_major_scale, modified_scale, "Jaccard", "pc"
)
print(f"Jaccard similarity between pitch classes: {pc_similarity:.4f}")

print("\n" + "=" * 50)
print("Batch comparison with multiple methods and transformations:")
print("=" * 50)

# Comprehensive comparison using multiple methods and transformations
comprehensive_results = get_similarity_batch(
    {"melody1": c_major_scale, "melody2": modified_scale},
    method=["Jaccard", "Dice", "cosine"],
    transformation=["pitch", "int", "parsons"],
)

for (name1, name2, method, transformation), similarity in comprehensive_results.items():
    print(f"{method} similarity ({transformation}): {similarity:.4f}")
