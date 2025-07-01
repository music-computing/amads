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


def ensure_dependencies():
    """Check and install dependencies if needed."""
    try:
        check_r_packages_installed(install_missing=False)
        return "All R packages are already installed."
    except ImportError:
        install_dependencies()
        return "Missing R packages installed successfully."


def create_test_melodies():
    """Create test melodies for demonstrations."""
    # Create a C major scale melody as (pitch, duration) tuples
    # Using MIDI note numbers: C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72

    c_major_scale = Score.from_melody(
        pitches=[60, 62, 64, 65, 67, 69, 71, 72],
        durations=1.0,  # C4 to C5  # quarter notes
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

    return {
        "c_major_scale": c_major_scale,
        "modified_scale": modified_scale,
        "third_scale": third_scale,
        "fourth_scale": fourth_scale,
    }


def demo_simple_similarity():
    """Demonstrate simple similarity comparison between two melodies."""
    melodies = create_test_melodies()
    c_major_scale = melodies["c_major_scale"]
    modified_scale = melodies["modified_scale"]

    similarity = get_similarity_from_scores(
        c_major_scale, modified_scale, "Jaccard", "pitch"
    )
    return {
        "method": "Jaccard",
        "transformation": "pitch",
        "similarity": similarity,
        "comparison": "c_major_scale vs modified_scale",
    }


def demo_batch_similarity():
    """Demonstrate batch similarity comparison across multiple melodies."""
    melodies = create_test_melodies()

    # Perform pairwise comparisons using 'cosine' and 'Simpson' similarity measures
    batch_results = get_similarity_batch(
        melodies, method=["cosine", "Simpson"], transformation="pitch"
    )

    # Organize results by similarity measure
    organized_results = {}
    for method in ["cosine", "Simpson"]:
        organized_results[method] = {}
        for (
            name1,
            name2,
            sim_method,
            transformation,
        ), similarity in batch_results.items():
            if sim_method == method:
                organized_results[method][f"{name1}_vs_{name2}"] = similarity

    return organized_results


def demo_transformations():
    """Demonstrate different transformation types."""
    melodies = create_test_melodies()
    c_major_scale = melodies["c_major_scale"]
    modified_scale = melodies["modified_scale"]

    results = {}

    # Intervallic similarity - should be different since we changed notes
    results["intervallic"] = get_similarity_from_scores(
        c_major_scale, modified_scale, "Euclidean", "int"
    )

    # IOI class similarity - should be 1.0 since all durations are the same
    results["ioi_class"] = get_similarity_from_scores(
        c_major_scale, modified_scale, "Jaccard", "ioi_class"
    )

    # Parsons code similarity - compares up/down patterns
    results["parsons"] = get_similarity_from_scores(
        c_major_scale, modified_scale, "Jaccard", "parsons"
    )

    # Pitch class similarity - ignores octaves
    results["pitch_class"] = get_similarity_from_scores(
        c_major_scale, modified_scale, "Jaccard", "pc"
    )

    return results


def demo_comprehensive_comparison():
    """Demonstrate comprehensive comparison with multiple methods and transformations."""
    melodies = create_test_melodies()
    c_major_scale = melodies["c_major_scale"]
    modified_scale = melodies["modified_scale"]

    # Comprehensive comparison using multiple methods and transformations
    comprehensive_results = get_similarity_batch(
        {"melody1": c_major_scale, "melody2": modified_scale},
        method=["Jaccard", "Dice", "cosine"],
        transformation=["pitch", "int", "parsons"],
    )

    # Organize results in a more readable format
    organized = {}
    for (
        name1,
        name2,
        method,
        transformation,
    ), similarity in comprehensive_results.items():
        key = f"{method}_{transformation}"
        organized[key] = similarity

    return organized


def run_all_demos():
    """Run all demonstration functions and return results."""
    print("Checking dependencies...")
    dep_status = ensure_dependencies()
    print(dep_status)

    print("\n" + "=" * 50)
    print("Simple Similarity Demo")
    print("=" * 50)
    simple_result = demo_simple_similarity()
    print(
        f"Jaccard similarity between c_major_scale and modified_scale: {simple_result['similarity']}"
    )

    print("\n" + "=" * 50)
    print("Batch Similarity Demo")
    print("=" * 50)
    batch_results = demo_batch_similarity()
    for method, comparisons in batch_results.items():
        print(f"\nPairwise {method} similarities:")
        for comparison, similarity in comparisons.items():
            print(f"  {comparison}: {similarity:.4f}")

    print("\n" + "=" * 50)
    print("Transformations Demo")
    print("=" * 50)
    transformation_results = demo_transformations()
    for transformation, similarity in transformation_results.items():
        print(f"{transformation} similarity: {similarity:.4f}")

    print("\n" + "=" * 50)
    print("Comprehensive Comparison Demo")
    print("=" * 50)
    comprehensive_results = demo_comprehensive_comparison()
    for method_transform, similarity in comprehensive_results.items():
        method, transform = method_transform.split("_", 1)
        print(f"{method} similarity ({transform}): {similarity:.4f}")

    return {
        "dependencies": dep_status,
        "simple": simple_result,
        "batch": batch_results,
        "transformations": transformation_results,
        "comprehensive": comprehensive_results,
    }


if __name__ == "__main__":
    run_all_demos()
