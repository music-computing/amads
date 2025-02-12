from amads.algorithms.mtype_tokenizer import FantasticTokenizer
from amads.core.basics import Part, Score


def example_usage():
    """Example usage of the MType tokenizer.

    This shows how to tokenize a melody into melodic types (mtypes)
    and count n-grams of the resulting tokens.
    """

    # Initialize the tokenizer and other AMADS objects
    tokenizer = FantasticTokenizer()
    score = Score()
    part = Part()
    score.insert(part)

    # Add notes with different pitches and durations
    melody_1 = Score.from_melody(
        pitches=[60, 62, 64, 67, 72],  # C4, D4, E4, G4, C5
        durations=[
            1.0,
            0.5,
            1.0,
            2.0,
            1.0,
        ],  # quarter, eighth, quarter, half, quarter notes
    )

    notes, iois, ioi_ratios = tokenizer.get_notes(melody_1)

    # the output of segment_melody is not used
    _ = tokenizer.segment_melody(notes, iois, ioi_ratios)
    mtypes = tokenizer.tokenize_phrase(notes, ioi_ratios)

    # Count bigrams (n=2)
    bigram_counts = tokenizer.count_grams(mtypes, n=2)
    print(bigram_counts)


if __name__ == "__main__":
    example_usage()

# TODO:
# get_mtype_counts should be the top level function, taking a Score object as input
# and returning a dictionary of mtype counts
# perhaps the best interface would be to have a method argument that specifies
# the n-gram length, so "all", 1, 2, 3, etc.
